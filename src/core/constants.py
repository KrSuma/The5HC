"""
Core business constants and enums
"""
from enum import Enum


class Gender(str, Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"


class TestType(str, Enum):
    """Assessment test types"""
    OVERHEAD_SQUAT = "overhead_squat"
    PUSH_UP = "push_up"
    SINGLE_LEG_BALANCE = "single_leg_balance"
    TOE_TOUCH = "toe_touch"
    SHOULDER_MOBILITY = "shoulder_mobility"
    FARMER_CARRY = "farmer_carry"
    HARVARD_STEP_TEST = "harvard_step_test"


class ScoreCategory(str, Enum):
    """Score categories"""
    STRENGTH = "strength"
    MOBILITY = "mobility"
    BALANCE = "balance"
    CARDIO = "cardio"
    OVERALL = "overall"


class FitnessLevel(str, Enum):
    """Fitness level classifications"""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


# Scoring thresholds
SCORE_THRESHOLDS = {
    FitnessLevel.EXCELLENT: 85,
    FitnessLevel.GOOD: 70,
    FitnessLevel.FAIR: 50,
    FitnessLevel.POOR: 0
}

# Test weights for overall score calculation
TEST_WEIGHTS = {
    ScoreCategory.STRENGTH: 0.3,
    ScoreCategory.MOBILITY: 0.25,
    ScoreCategory.BALANCE: 0.25,
    ScoreCategory.CARDIO: 0.2
}

# Authentication constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 5
SESSION_TIMEOUT_MINUTES = 60

# PDF generation constants
PDF_FONT_FAMILY = "NanumGothic"
PDF_TITLE_FONT_SIZE = 24
PDF_HEADING_FONT_SIZE = 16
PDF_BODY_FONT_SIZE = 12

# Database constants
DATABASE_NAME = "fitness_assessment.db"
DATABASE_BACKUP_PREFIX = "fitness_assessment.db.backup_"