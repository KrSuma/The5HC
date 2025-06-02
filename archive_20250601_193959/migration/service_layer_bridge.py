# service_layer_bridge.py - Bridge between old service layer and new secure modules

from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

# Import the new secure modules
from improved_service_layer import (
    AuthService as SecureAuthService,
    ClientService as SecureClientService,
    AssessmentService as SecureAssessmentService,
    DashboardService as SecureDashboardService,
    AnalyticsService as SecureAnalyticsService,
    AppInitService as SecureAppInitService
)

# Import old database functions for compatibility
from improved_db_utils import init_db as old_init_db


class AuthService:
    """Bridge for authentication service"""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[int]:
        """Authenticate a user with username and password"""
        success, message = SecureAuthService.login(username, password)
        if success:
            # Return trainer_id from session state
            import streamlit as st
            return st.session_state.get('trainer_id')
        return None
    
    @staticmethod
    def register_user(username: str, password: str, name: str, email: str) -> bool:
        """Register a new trainer"""
        success, message = SecureAuthService.register(username, password, name, email)
        return success


class ClientService:
    """Bridge for client operations"""
    
    @staticmethod
    def add_new_client(trainer_id: int, name: str, age: int, gender: str, 
                      height: float, weight: float, email: str = "", phone: str = "") -> int:
        """Add a new client"""
        success, message = SecureClientService.add_client(
            trainer_id, name, age, gender, height, weight, email, phone
        )
        if success:
            # Get the newly created client ID
            clients = SecureClientService.get_trainer_clients(trainer_id)
            for client_id, client_name in clients:
                if client_name == name:
                    return client_id
        return 0
    
    @staticmethod
    def get_clients_for_trainer(trainer_id: int) -> List[Tuple[int, str]]:
        """Get all clients for a trainer"""
        return SecureClientService.get_trainer_clients(trainer_id)
    
    @staticmethod
    def get_client_info(client_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed client information"""
        return SecureClientService.get_client_details(client_id)
    
    @staticmethod
    def calculate_bmi(height: float, weight: float) -> float:
        """Calculate BMI from height and weight"""
        if height > 0:
            height_m = height / 100
            return round(weight / (height_m ** 2), 1)
        return 0.0


class AssessmentService:
    """Bridge for assessment operations"""
    
    @staticmethod
    def save_new_assessment(assessment_data: Dict[str, Any]) -> int:
        """Save a new assessment"""
        success, message = SecureAssessmentService.save_assessment(assessment_data)
        if success:
            # Return a dummy ID for now
            return 1
        return 0
    
    @staticmethod
    def get_assessments_for_client(client_id: int) -> List[Dict[str, Any]]:
        """Get all assessments for a client"""
        return SecureAssessmentService.get_client_assessments(client_id)
    
    @staticmethod
    def get_assessment_info(assessment_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed assessment information"""
        return SecureAssessmentService.get_assessment_details(assessment_id)


class DashboardService:
    """Bridge for dashboard operations"""
    
    @staticmethod
    def get_recent_assessments_for_trainer(trainer_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent assessments for a trainer"""
        # Use the secure dashboard service
        stats = SecureDashboardService.get_trainer_stats(trainer_id)
        # For now, return empty list as we don't have a direct equivalent
        return []
    
    @staticmethod
    def get_trainer_statistics(trainer_id: int) -> Dict[str, Any]:
        """Get statistics for a trainer"""
        return SecureDashboardService.get_trainer_stats(trainer_id)
    
    @staticmethod
    def search_clients_by_name(trainer_id: int, search_term: str) -> List[Dict[str, Any]]:
        """Search clients by name"""
        return SecureDashboardService.search_clients(trainer_id, search_term)


class AnalyticsService:
    """Bridge for analytics operations"""
    
    @staticmethod
    def get_progress_data(client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get progress data for a client"""
        return SecureAnalyticsService.get_client_progress(client_id, limit)
    
    @staticmethod
    def identify_asymmetries(assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify asymmetries in assessment"""
        return SecureAnalyticsService.detect_asymmetries(assessment)
    
    @staticmethod
    def get_priority_areas(assessment: Dict[str, Any]) -> List[str]:
        """Get priority areas for improvement"""
        return SecureAnalyticsService.identify_priority_areas(assessment)


class AppInitService:
    """Bridge for application initialization"""
    
    @staticmethod
    def initialize_app():
        """Initialize the application"""
        SecureAppInitService.initialize()
    
    @staticmethod
    def check_fonts_availability() -> Dict[str, bool]:
        """Check if required fonts are available"""
        from pathlib import Path
        from config import config
        
        return {
            'NanumGothic.ttf': Path(config.ui.font_regular).exists(),
            'NanumGothicBold.ttf': Path(config.ui.font_bold).exists()
        }


# For backward compatibility, keep the old init_db function
def init_db():
    """Initialize database (for backward compatibility)"""
    old_init_db()