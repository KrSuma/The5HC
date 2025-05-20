# service_layer.py - Service layer to separate UI from database operations

from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

# Import the database functions from improved_db_utils
from improved_db_utils import (
    init_db, authenticate, register_trainer, add_client, get_clients,
    get_client_details, save_assessment, get_client_assessments,
    get_assessment_details, get_recent_assessments, get_trainer_stats
)

class AuthService:
    """Authentication service for trainers"""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[int]:
        """
        Authenticate a user with username and password
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            int: Trainer ID if successful, None otherwise
        """
        return authenticate(username, password)
    
    @staticmethod
    def register_user(username: str, password: str, name: str, email: str) -> bool:
        """
        Register a new trainer
        
        Args:
            username: Username for the new trainer
            password: Password for the new trainer
            name: Name of the new trainer
            email: Email of the new trainer
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        return register_trainer(username, password, name, email)


class ClientService:
    """Service for client operations"""
    
    @staticmethod
    def add_new_client(trainer_id: int, name: str, age: int, gender: str, 
                    height: float, weight: float, email: str, phone: str) -> Optional[int]:
        """
        Add a new client for a trainer
        
        Args:
            trainer_id: ID of the trainer adding the client
            name: Name of the client
            age: Age of the client
            gender: Gender of the client
            height: Height in cm
            weight: Weight in kg
            email: Email of the client
            phone: Phone number of the client
            
        Returns:
            int: Client ID if successful, None otherwise
        """
        return add_client(trainer_id, name, age, gender, height, weight, email, phone)
    
    @staticmethod
    def get_trainer_clients(trainer_id: int) -> List[Tuple[int, str]]:
        """
        Get all clients for a trainer
        
        Args:
            trainer_id: ID of the trainer
            
        Returns:
            List[Tuple[int, str]]: List of client IDs and names
        """
        return get_clients(trainer_id)
    
    @staticmethod
    def get_client(client_id: int) -> Optional[Dict[str, Any]]:
        """
        Get details for a client
        
        Args:
            client_id: ID of the client
            
        Returns:
            Dict[str, Any]: Client details if found, None otherwise
        """
        return get_client_details(client_id)
    
    @staticmethod
    def calculate_bmi(client: Dict[str, Any]) -> float:
        """
        Calculate BMI for a client
        
        Args:
            client: Client dictionary with height and weight
            
        Returns:
            float: BMI value
        """
        if 'height' in client and 'weight' in client:
            height_m = client['height'] / 100  # Convert cm to m
            weight_kg = client['weight']
            return weight_kg / (height_m * height_m)
        return 0.0


class AssessmentService:
    """Service for assessment operations"""
    
    @staticmethod
    def save_new_assessment(assessment_data: Dict[str, Any]) -> Optional[int]:
        """
        Save a new assessment
        
        Args:
            assessment_data: Assessment data to save
            
        Returns:
            int: Assessment ID if successful, None otherwise
        """
        # Ensure date is set
        if 'date' not in assessment_data:
            assessment_data['date'] = datetime.now().strftime("%Y-%m-%d")
            
        return save_assessment(assessment_data)
    
    @staticmethod
    def get_client_assessment_history(client_id: int) -> List[Tuple[int, str, float]]:
        """
        Get assessment history for a client
        
        Args:
            client_id: ID of the client
            
        Returns:
            List[Tuple[int, str, float]]: List of assessment IDs, dates, and scores
        """
        return get_client_assessments(client_id)
    
    @staticmethod
    def get_assessment(assessment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get details for an assessment
        
        Args:
            assessment_id: ID of the assessment
            
        Returns:
            Dict[str, Any]: Assessment details if found, None otherwise
        """
        return get_assessment_details(assessment_id)


class DashboardService:
    """Service for dashboard operations"""
    
    @staticmethod
    def get_recent_assessments(trainer_id: int, limit: int = 10) -> List[Tuple[int, str, str, float]]:
        """
        Get recent assessments for a trainer
        
        Args:
            trainer_id: ID of the trainer
            limit: Maximum number of assessments to return
            
        Returns:
            List[Tuple[int, str, str, float]]: List of assessment IDs, client names, dates, and scores
        """
        return get_recent_assessments(trainer_id, limit)
    
    @staticmethod
    def get_trainer_statistics(trainer_id: int) -> Dict[str, int]:
        """
        Get statistics for a trainer
        
        Args:
            trainer_id: ID of the trainer
            
        Returns:
            Dict[str, int]: Dictionary with statistics
        """
        return get_trainer_stats(trainer_id)
    
    @staticmethod
    def search_assessments(trainer_id: int, search_criteria: Dict[str, Any]) -> List[Tuple[int, str, str, float]]:
        """
        Search assessments for a trainer based on criteria
        
        Args:
            trainer_id: ID of the trainer
            search_criteria: Dictionary with search criteria
            
        Returns:
            List[Tuple[int, str, str, float]]: List of matching assessments
        """
        # This would typically query the database with filters
        # For now, we'll get all assessments and filter in Python
        all_assessments = get_recent_assessments(trainer_id, limit=1000)  # Get more to filter
        
        filtered_assessments = []
        for assessment in all_assessments:
            assessment_id, client_name, date, score = assessment
            
            # Check each criterion
            include = True
            
            if 'client_id' in search_criteria:
                # This would require modifying get_recent_assessments to include client_id
                # For now, we'll skip this filter
                pass
                
            if 'date_start' in search_criteria and 'date_end' in search_criteria:
                if not (search_criteria['date_start'] <= date <= search_criteria['date_end']):
                    include = False
                    
            if 'score_min' in search_criteria and 'score_max' in search_criteria:
                if not (search_criteria['score_min'] <= score <= search_criteria['score_max']):
                    include = False
            
            if include:
                filtered_assessments.append(assessment)
        
        return filtered_assessments


# Initialize database on import
init_db()


class AnalyticsService:
    """Service for analytics and reporting operations"""
    
    @staticmethod
    def get_client_progress(client_id: int) -> Dict[str, Any]:
        """
        Get progress data for a client across multiple assessments
        
        Args:
            client_id: ID of the client
            
        Returns:
            Dict[str, Any]: Progress data
        """
        assessments = get_client_assessments(client_id)
        
        if not assessments:
            return {
                'dates': [],
                'overall_scores': [],
                'category_scores': {
                    'strength': [],
                    'mobility': [],
                    'balance': [],
                    'cardio': []
                }
            }
        
        # Get full details for each assessment
        assessment_details = []
        for assessment_id, _, _ in assessments:
            details = get_assessment_details(assessment_id)
            if details:
                assessment_details.append(details)
        
        # Sort by date
        assessment_details.sort(key=lambda x: x['date'])
        
        # Extract progress data
        progress_data = {
            'dates': [a['date'] for a in assessment_details],
            'overall_scores': [a['overall_score'] for a in assessment_details],
            'category_scores': {
                'strength': [a['strength_score'] for a in assessment_details],
                'mobility': [a['mobility_score'] for a in assessment_details],
                'balance': [a['balance_score'] for a in assessment_details],
                'cardio': [a['cardio_score'] for a in assessment_details]
            },
            'test_scores': {
                'overhead_squat': [a['overhead_squat_score'] for a in assessment_details],
                'push_up': [a['push_up_score'] for a in assessment_details],
                'shoulder_mobility': [a['shoulder_mobility_score'] for a in assessment_details],
                'farmers_carry': [a['farmers_carry_score'] for a in assessment_details],
                'step_test': [a['step_test_score'] for a in assessment_details]
            }
        }
        
        return progress_data
    
    @staticmethod
    def analyze_asymmetries(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze bilateral asymmetries in the assessment data
        
        Args:
            assessment_data: Assessment data to analyze
            
        Returns:
            Dict[str, Any]: Asymmetry analysis
        """
        asymmetries = {}
        
        # Single Leg Balance asymmetry
        if all(k in assessment_data for k in ['single_leg_balance_right_open', 'single_leg_balance_left_open',
                                            'single_leg_balance_right_closed', 'single_leg_balance_left_closed']):
            right_open = assessment_data['single_leg_balance_right_open']
            left_open = assessment_data['single_leg_balance_left_open']
            right_closed = assessment_data['single_leg_balance_right_closed']
            left_closed = assessment_data['single_leg_balance_left_closed']
            
            open_diff = abs(right_open - left_open)
            closed_diff = abs(right_closed - left_closed)
            
            asymmetries['balance'] = {
                'open_eyes_difference': open_diff,
                'closed_eyes_difference': closed_diff,
                'significant': open_diff > 5 or closed_diff > 5,
                'weaker_side': 'right' if (right_open + right_closed) < (left_open + left_closed) else 'left'
            }
        
        # Shoulder Mobility asymmetry
        if all(k in assessment_data for k in ['shoulder_mobility_right', 'shoulder_mobility_left']):
            right_mobility = assessment_data['shoulder_mobility_right']
            left_mobility = assessment_data['shoulder_mobility_left']
            
            mobility_diff = abs(right_mobility - left_mobility)
            
            asymmetries['shoulder'] = {
                'difference': mobility_diff,
                'significant': mobility_diff >= 0.5,
                'tighter_side': 'right' if right_mobility > left_mobility else 'left'
            }
        
        return asymmetries
    
    @staticmethod
    def identify_priority_areas(assessment_data: Dict[str, Any]) -> List[str]:
        """
        Identify priority areas for improvement based on assessment data
        
        Args:
            assessment_data: Assessment data to analyze
            
        Returns:
            List[str]: Priority areas for improvement
        """
        priorities = []
        
        # Check for very low scores in each category
        if assessment_data.get('strength_score', 25) < 12.5:  # Less than 50% of max
            priorities.append('strength')
        
        if assessment_data.get('mobility_score', 25) < 12.5:
            priorities.append('mobility')
            
        if assessment_data.get('balance_score', 25) < 12.5:
            priorities.append('balance')
            
        if assessment_data.get('cardio_score', 25) < 12.5:
            priorities.append('cardio')
        
        # Check for significant asymmetries
        asymmetries = AnalyticsService.analyze_asymmetries(assessment_data)
        if asymmetries.get('balance', {}).get('significant', False):
            priorities.append('balance_asymmetry')
            
        if asymmetries.get('shoulder', {}).get('significant', False):
            priorities.append('shoulder_asymmetry')
        
        # Check for pain reported in any test
        if assessment_data.get('overhead_squat_score', 3) == 0:
            priorities.append('squat_pain')
            
        if assessment_data.get('shoulder_mobility_score', 3) == 0:
            priorities.append('shoulder_pain')
        
        return priorities


class AppInitService:
    """Service for application initialization"""
    
    @staticmethod
    def initialize_app():
        """Initialize the application"""
        # Initialize database
        init_db()
        
    @staticmethod
    def check_fonts_availability() -> Dict[str, bool]:
        """
        Check if required fonts are available
        
        Returns:
            Dict[str, bool]: Dictionary indicating which fonts are available
        """
        import os
        
        fonts = {
            'NanumGothic': os.path.exists('NanumGothic.ttf'),
            'NanumGothicBold': os.path.exists('NanumGothicBold.ttf')
        }
        
        return fonts