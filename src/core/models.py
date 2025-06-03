"""
Core domain models for the fitness assessment system
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BaseEntity:
    """Base class for all entities"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass 
class Trainer(BaseEntity):
    """Trainer entity"""
    username: str = ""
    password_hash: str = ""
    name: str = ""
    email: str = ""
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class Client(BaseEntity):
    """Client entity"""
    trainer_id: int = 0
    name: str = ""
    age: int = 0
    gender: str = ""
    height: float = 0.0
    weight: float = 0.0
    email: Optional[str] = ""
    phone: Optional[str] = ""
    
    @property
    def bmi(self) -> float:
        """Calculate BMI"""
        if self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return 0.0


@dataclass
class Assessment(BaseEntity):
    """Assessment entity"""
    client_id: int = 0
    trainer_id: int = 0
    date: str = ""
    
    # Test scores
    overhead_squat_score: Optional[int] = None
    overhead_squat_notes: Optional[str] = ""
    overhead_squat_compensations: Optional[str] = ""
    
    push_up_score: Optional[int] = None
    push_up_reps: Optional[int] = None
    push_up_notes: Optional[str] = ""
    push_up_compensations: Optional[str] = ""
    
    single_leg_balance_left_eyes_open: Optional[float] = None
    single_leg_balance_right_eyes_open: Optional[float] = None
    single_leg_balance_left_eyes_closed: Optional[float] = None
    single_leg_balance_right_eyes_closed: Optional[float] = None
    single_leg_balance_notes: Optional[str] = ""
    
    toe_touch_score: Optional[int] = None
    toe_touch_distance: Optional[float] = None
    toe_touch_notes: Optional[str] = ""
    toe_touch_compensations: Optional[str] = ""
    
    shoulder_mobility_left: Optional[float] = None
    shoulder_mobility_right: Optional[float] = None
    shoulder_mobility_score: Optional[int] = None
    shoulder_mobility_notes: Optional[str] = ""
    shoulder_mobility_compensations: Optional[str] = ""
    
    farmer_carry_weight: Optional[float] = None
    farmer_carry_distance: Optional[float] = None
    farmer_carry_score: Optional[int] = None
    farmer_carry_notes: Optional[str] = ""
    farmer_carry_compensations: Optional[str] = ""
    
    harvard_step_test_heart_rate: Optional[int] = None
    harvard_step_test_duration: Optional[float] = None
    harvard_step_test_notes: Optional[str] = ""
    
    # Category scores
    overall_score: Optional[float] = None
    strength_score: Optional[float] = None
    mobility_score: Optional[float] = None
    balance_score: Optional[float] = None
    cardio_score: Optional[float] = None