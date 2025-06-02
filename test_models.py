"""
Tests for database abstraction layer
"""
import pytest
from datetime import datetime
from models import (
    TrainerRepository, ClientRepository, AssessmentRepository,
    Trainer, Client, Assessment,
    UnitOfWork, RepositoryFactory
)


class TestEntities:
    """Test entity classes"""
    
    def test_trainer_entity(self):
        """Test Trainer entity creation"""
        trainer = Trainer(
            username="testuser",
            password_hash="hashed_password",
            name="Test User",
            email="test@example.com"
        )
        
        assert trainer.username == "testuser"
        assert trainer.password_hash == "hashed_password"
        assert trainer.name == "Test User"
        assert trainer.email == "test@example.com"
        assert trainer.failed_login_attempts == 0
    
    def test_client_entity(self):
        """Test Client entity with BMI calculation"""
        client = Client(
            trainer_id=1,
            name="Test Client",
            age=30,
            gender="Male",
            height=175.0,
            weight=75.0
        )
        
        assert client.trainer_id == 1
        assert client.name == "Test Client"
        assert client.bmi == 24.5  # 75 / (1.75^2)
    
    def test_assessment_entity(self):
        """Test Assessment entity creation"""
        assessment = Assessment(
            client_id=1,
            trainer_id=1,
            date="2024-01-01",
            overall_score=75.0
        )
        
        assert assessment.client_id == 1
        assert assessment.trainer_id == 1
        assert assessment.date == "2024-01-01"
        assert assessment.overall_score == 75.0


class TestRepositories:
    """Test repository implementations"""
    
    @pytest.fixture
    def setup_test_db(self, tmp_path):
        """Set up test database"""
        # Override database path
        from database import DatabaseConfig
        original_path = DatabaseConfig.DB_PATH
        DatabaseConfig.DB_PATH = str(tmp_path / "test.db")
        
        # Initialize database
        from database import init_db
        init_db()
        
        yield
        
        # Cleanup
        DatabaseConfig.DB_PATH = original_path
    
    def test_trainer_repository(self, setup_test_db):
        """Test TrainerRepository operations"""
        repo = TrainerRepository()
        
        # Create trainer
        trainer = Trainer(
            username="repotest",
            password_hash="hashed",
            name="Repo Test",
            email="repo@test.com"
        )
        
        trainer_id = repo.create(trainer)
        assert trainer_id is not None
        
        # Get by ID
        fetched = repo.get_by_id(trainer_id)
        assert fetched is not None
        assert fetched.username == "repotest"
        
        # Get by username
        fetched = repo.get_by_username("repotest")
        assert fetched is not None
        assert fetched.id == trainer_id
        
        # Update trainer
        fetched.name = "Updated Name"
        success = repo.update(fetched)
        assert success == True
        
        # Verify update
        updated = repo.get_by_id(trainer_id)
        assert updated.name == "Updated Name"
    
    def test_client_repository(self, setup_test_db):
        """Test ClientRepository operations"""
        # First create a trainer
        trainer_repo = TrainerRepository()
        trainer = Trainer(
            username="trainer1",
            password_hash="hashed",
            name="Trainer One",
            email="trainer1@test.com"
        )
        trainer_id = trainer_repo.create(trainer)
        
        # Test client operations
        client_repo = ClientRepository()
        
        # Create client
        client = Client(
            trainer_id=trainer_id,
            name="Test Client",
            age=25,
            gender="Female",
            height=165.0,
            weight=60.0,
            email="client@test.com"
        )
        
        client_id = client_repo.create(client)
        assert client_id is not None
        
        # Get by ID
        fetched = client_repo.get_by_id(client_id)
        assert fetched is not None
        assert fetched.name == "Test Client"
        assert fetched.bmi == 22.0  # 60 / (1.65^2)
        
        # Get by trainer
        clients = client_repo.get_by_trainer(trainer_id)
        assert len(clients) == 1
        assert clients[0].id == client_id
        
        # Search
        results = client_repo.search(trainer_id, "Test")
        assert len(results) == 1
        
        results = client_repo.search(trainer_id, "client@test")
        assert len(results) == 1
        
        results = client_repo.search(trainer_id, "nonexistent")
        assert len(results) == 0
    
    def test_assessment_repository(self, setup_test_db):
        """Test AssessmentRepository operations"""
        # Create trainer and client first
        trainer_repo = TrainerRepository()
        trainer = Trainer(
            username="trainer2",
            password_hash="hashed",
            name="Trainer Two",
            email="trainer2@test.com"
        )
        trainer_id = trainer_repo.create(trainer)
        
        client_repo = ClientRepository()
        client = Client(
            trainer_id=trainer_id,
            name="Assessment Client",
            age=30,
            gender="Male",
            height=180.0,
            weight=80.0
        )
        client_id = client_repo.create(client)
        
        # Test assessment operations
        assessment_repo = AssessmentRepository()
        
        # Create assessment
        assessment = Assessment(
            client_id=client_id,
            trainer_id=trainer_id,
            date="2024-01-01",
            overhead_squat_score=2,
            push_up_score=3,
            push_up_reps=25,
            overall_score=75.0,
            strength_score=20.0,
            mobility_score=18.0,
            balance_score=19.0,
            cardio_score=18.0
        )
        
        assessment_id = assessment_repo.create(assessment)
        assert assessment_id is not None
        
        # Get by ID
        fetched = assessment_repo.get_by_id(assessment_id)
        assert fetched is not None
        assert fetched.overall_score == 75.0
        
        # Get by client
        assessments = assessment_repo.get_by_client(client_id)
        assert len(assessments) == 1
        assert assessments[0].id == assessment_id
        
        # Get latest
        latest = assessment_repo.get_latest_by_client(client_id)
        assert latest is not None
        assert latest.id == assessment_id
        
        # Get progress
        progress = assessment_repo.get_progress(client_id)
        assert len(progress) == 1
        assert progress[0]['overall_score'] == 75.0


class TestUnitOfWork:
    """Test Unit of Work pattern"""
    
    @pytest.fixture
    def setup_test_db(self, tmp_path):
        """Set up test database"""
        from database import DatabaseConfig
        original_path = DatabaseConfig.DB_PATH
        DatabaseConfig.DB_PATH = str(tmp_path / "test.db")
        
        from database import init_db
        init_db()
        
        yield
        
        DatabaseConfig.DB_PATH = original_path
    
    def test_unit_of_work_commit(self, setup_test_db):
        """Test UoW with successful commit"""
        with UnitOfWork() as uow:
            # Create trainer
            trainer = Trainer(
                username="uowtest",
                password_hash="hashed",
                name="UoW Test",
                email="uow@test.com"
            )
            trainer_id = uow.trainers.create(trainer)
            
            # Create client
            client = Client(
                trainer_id=trainer_id,
                name="UoW Client",
                age=25,
                gender="Male",
                height=170.0,
                weight=70.0
            )
            client_id = uow.clients.create(client)
            
            assert trainer_id is not None
            assert client_id is not None
        
        # Verify data was committed
        trainer_repo = TrainerRepository()
        trainer = trainer_repo.get_by_username("uowtest")
        assert trainer is not None
    
    def test_unit_of_work_rollback(self, setup_test_db):
        """Test UoW with rollback on error"""
        try:
            with UnitOfWork() as uow:
                # Create trainer
                trainer = Trainer(
                    username="rollbacktest",
                    password_hash="hashed",
                    name="Rollback Test",
                    email="rollback@test.com"
                )
                trainer_id = uow.trainers.create(trainer)
                
                # Force an error
                raise Exception("Test error")
                
        except Exception:
            pass
        
        # Verify data was rolled back
        trainer_repo = TrainerRepository()
        trainer = trainer_repo.get_by_username("rollbacktest")
        assert trainer is None


class TestRepositoryFactory:
    """Test repository factory"""
    
    def test_factory_singleton(self):
        """Test that factory returns singleton instances"""
        # Get repositories multiple times
        repo1 = RepositoryFactory.get_trainer_repository()
        repo2 = RepositoryFactory.get_trainer_repository()
        
        # Should be same instance
        assert repo1 is repo2
        
        # Test for other repositories
        client_repo1 = RepositoryFactory.get_client_repository()
        client_repo2 = RepositoryFactory.get_client_repository()
        assert client_repo1 is client_repo2
        
        assessment_repo1 = RepositoryFactory.get_assessment_repository()
        assessment_repo2 = RepositoryFactory.get_assessment_repository()
        assert assessment_repo1 is assessment_repo2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])