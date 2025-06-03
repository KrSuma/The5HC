"""
Assessment management service
"""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from ..core.models import Assessment, Client
from ..core.scoring import calculate_scores
from ..core.recommendations import generate_recommendations
from ..data.repositories import RepositoryFactory
from ..data.cache import AssessmentCache
from ..utils.logging import audit_logger, error_logger, app_logger
# TODO: Import log_execution_time once logging is properly organized
from ..utils.validators import sanitize_input


class AssessmentService:
    """Service for managing fitness assessments"""
    
    def __init__(self):
        self.assessment_repo = RepositoryFactory.get_assessment_repository()
        self.client_repo = RepositoryFactory.get_client_repository()
        self.assessment_cache = AssessmentCache()
    
    def create_assessment(self, client_id: int, trainer_id: int, 
                         assessment_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Create new assessment with automatic scoring"""
        try:
            # Validate client belongs to trainer
            client = self.client_repo.get_by_id(client_id)
            if not client or client.trainer_id != trainer_id:
                return False, "권한이 없거나 고객을 찾을 수 없습니다.", None
            
            # Calculate scores
            scores = calculate_scores(client, assessment_data)
            
            # Create assessment entity
            assessment = Assessment(
                client_id=client_id,
                trainer_id=trainer_id,
                date=datetime.now().strftime("%Y-%m-%d"),
                **assessment_data,
                **scores
            )
            
            # Sanitize text fields
            if assessment.overhead_squat_notes:
                assessment.overhead_squat_notes = sanitize_input(assessment.overhead_squat_notes, 500)
            if assessment.push_up_notes:
                assessment.push_up_notes = sanitize_input(assessment.push_up_notes, 500)
            if assessment.single_leg_balance_notes:
                assessment.single_leg_balance_notes = sanitize_input(assessment.single_leg_balance_notes, 500)
            if assessment.toe_touch_notes:
                assessment.toe_touch_notes = sanitize_input(assessment.toe_touch_notes, 500)
            if assessment.shoulder_mobility_notes:
                assessment.shoulder_mobility_notes = sanitize_input(assessment.shoulder_mobility_notes, 500)
            if assessment.farmer_carry_notes:
                assessment.farmer_carry_notes = sanitize_input(assessment.farmer_carry_notes, 500)
            if assessment.harvard_step_test_notes:
                assessment.harvard_step_test_notes = sanitize_input(assessment.harvard_step_test_notes, 500)
            
            # Save assessment
            assessment_id = self.assessment_repo.create(assessment)
            
            if assessment_id:
                # Clear cache
                self.assessment_cache.invalidate_list(client_id)
                self.assessment_cache.invalidate_latest(client_id)
                
                app_logger.info(f"Assessment created for client {client_id} (ID: {assessment_id})")
                audit_logger.log_data_modification(trainer_id, 'assessment', assessment_id, {'action': 'create'})
                
                return True, "평가가 저장되었습니다.", assessment_id
            else:
                return False, "평가 저장 중 오류가 발생했습니다.", None
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'create_assessment', 'client_id': client_id})
            return False, "평가 저장 중 오류가 발생했습니다.", None
    
    def get_assessments(self, client_id: int) -> List[Assessment]:
        """Get all assessments for a client"""
        try:
            # Check cache first
            cached_assessments = self.assessment_cache.get_list(client_id)
            if cached_assessments is not None:
                return cached_assessments
            
            # Get from database
            assessments = self.assessment_repo.get_by_client(client_id)
            
            # Cache the results
            self.assessment_cache.set_list(client_id, assessments)
            
            return assessments
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_assessments', 'client_id': client_id})
            return []
    
    def get_assessment(self, assessment_id: int) -> Optional[Assessment]:
        """Get assessment by ID"""
        try:
            # Check cache first
            cached_assessment = self.assessment_cache.get(assessment_id)
            if cached_assessment:
                return cached_assessment
            
            # Get from database
            assessment = self.assessment_repo.get_by_id(assessment_id)
            
            if assessment:
                # Cache the result
                self.assessment_cache.set(assessment_id, assessment)
            
            return assessment
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_assessment', 'assessment_id': assessment_id})
            return None
    
    def get_latest_assessment(self, client_id: int) -> Optional[Assessment]:
        """Get latest assessment for a client"""
        try:
            # Check cache first
            cached_latest = self.assessment_cache.get_latest(client_id)
            if cached_latest:
                return cached_latest
            
            # Get from database
            assessment = self.assessment_repo.get_latest_by_client(client_id)
            
            if assessment:
                # Cache the result
                self.assessment_cache.set_latest(client_id, assessment)
                self.assessment_cache.set(assessment.id, assessment)
            
            return assessment
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_latest_assessment', 'client_id': client_id})
            return None
    
    def get_progress(self, client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get assessment progress data for charts"""
        try:
            return self.assessment_repo.get_progress(client_id, limit)
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_progress', 'client_id': client_id})
            return []
    
    def get_recommendations(self, assessment_id: int) -> Dict[str, List[str]]:
        """Get recommendations based on assessment"""
        try:
            assessment = self.get_assessment(assessment_id)
            if not assessment:
                return {}
            
            client = self.client_repo.get_by_id(assessment.client_id)
            if not client:
                return {}
            
            return generate_recommendations(assessment, client)
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_recommendations', 'assessment_id': assessment_id})
            return {}
    
    def compare_assessments(self, assessment_id1: int, assessment_id2: int) -> Dict[str, Any]:
        """Compare two assessments"""
        try:
            assessment1 = self.get_assessment(assessment_id1)
            assessment2 = self.get_assessment(assessment_id2)
            
            if not assessment1 or not assessment2:
                return {}
            
            # Calculate differences
            comparison = {
                'date1': assessment1.date,
                'date2': assessment2.date,
                'overall_change': assessment2.overall_score - assessment1.overall_score if assessment1.overall_score and assessment2.overall_score else 0,
                'strength_change': assessment2.strength_score - assessment1.strength_score if assessment1.strength_score and assessment2.strength_score else 0,
                'mobility_change': assessment2.mobility_score - assessment1.mobility_score if assessment1.mobility_score and assessment2.mobility_score else 0,
                'balance_change': assessment2.balance_score - assessment1.balance_score if assessment1.balance_score and assessment2.balance_score else 0,
                'cardio_change': assessment2.cardio_score - assessment1.cardio_score if assessment1.cardio_score and assessment2.cardio_score else 0,
            }
            
            # Add specific test comparisons
            if assessment1.push_up_reps and assessment2.push_up_reps:
                comparison['push_up_change'] = assessment2.push_up_reps - assessment1.push_up_reps
            
            if assessment1.farmer_carry_weight and assessment2.farmer_carry_weight:
                comparison['farmer_carry_weight_change'] = assessment2.farmer_carry_weight - assessment1.farmer_carry_weight
            
            return comparison
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'compare_assessments'})
            return {}
    
    def get_trainer_stats(self, trainer_id: int) -> Dict[str, Any]:
        """Get assessment statistics for all trainer's clients"""
        try:
            # Get all clients
            clients = self.client_repo.get_by_trainer(trainer_id)
            
            if not clients:
                return {
                    'total_assessments': 0,
                    'avg_overall_score': 0,
                    'improvement_rate': 0,
                    'most_improved_category': None
                }
            
            total_assessments = 0
            total_score = 0
            improvements = 0
            category_improvements = {
                'strength': 0,
                'mobility': 0,
                'balance': 0,
                'cardio': 0
            }
            
            for client in clients:
                assessments = self.get_assessments(client.id)
                total_assessments += len(assessments)
                
                if assessments:
                    # Latest assessment score
                    if assessments[0].overall_score:
                        total_score += assessments[0].overall_score
                    
                    # Check for improvement
                    if len(assessments) >= 2:
                        latest = assessments[0]
                        previous = assessments[1]
                        
                        if latest.overall_score and previous.overall_score:
                            if latest.overall_score > previous.overall_score:
                                improvements += 1
                            
                            # Category improvements
                            if latest.strength_score and previous.strength_score:
                                category_improvements['strength'] += latest.strength_score - previous.strength_score
                            if latest.mobility_score and previous.mobility_score:
                                category_improvements['mobility'] += latest.mobility_score - previous.mobility_score
                            if latest.balance_score and previous.balance_score:
                                category_improvements['balance'] += latest.balance_score - previous.balance_score
                            if latest.cardio_score and previous.cardio_score:
                                category_improvements['cardio'] += latest.cardio_score - previous.cardio_score
            
            # Calculate statistics
            avg_score = total_score / len(clients) if clients else 0
            improvement_rate = (improvements / len(clients)) * 100 if clients else 0
            most_improved = max(category_improvements.items(), key=lambda x: x[1])[0] if any(category_improvements.values()) else None
            
            return {
                'total_assessments': total_assessments,
                'avg_overall_score': round(avg_score, 1),
                'improvement_rate': round(improvement_rate, 1),
                'most_improved_category': most_improved
            }
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_trainer_stats', 'trainer_id': trainer_id})
            return {
                'total_assessments': 0,
                'avg_overall_score': 0,
                'improvement_rate': 0,
                'most_improved_category': None
            }