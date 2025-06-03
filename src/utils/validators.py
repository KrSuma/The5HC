"""
Input validation utilities
"""
import re
from typing import Optional


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitize and truncate input string"""
    if not value:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';()&+]', '', str(value))
    
    # Truncate to max length
    return sanitized[:max_length].strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (Korean format)"""
    if not phone:
        return False
    
    # Remove spaces and dashes
    clean_phone = re.sub(r'[\s-]', '', phone)
    
    # Korean phone number patterns
    patterns = [
        r'^010\d{8}$',  # Mobile: 010-xxxx-xxxx
        r'^02\d{7,8}$',  # Seoul: 02-xxx-xxxx or 02-xxxx-xxxx
        r'^0[3-9]\d{8,9}$',  # Other areas: 0xx-xxx-xxxx or 0xx-xxxx-xxxx
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def validate_password_strength(password: str, min_length: int = 8) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < min_length:
        return False, f"비밀번호는 최소 {min_length}자 이상이어야 합니다."
    
    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        return False, "비밀번호에는 최소 하나의 문자가 포함되어야 합니다."
    
    if not re.search(r'\d', password):
        return False, "비밀번호에는 최소 하나의 숫자가 포함되어야 합니다."
    
    # Check for common weak passwords
    weak_patterns = [
        r'password',
        r'123456',
        r'qwerty',
        r'admin',
        r'user'
    ]
    
    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            return False, "너무 단순한 비밀번호입니다."
    
    return True, "비밀번호가 유효합니다."


def validate_age(age: int) -> bool:
    """Validate age range"""
    return 1 <= age <= 120


def validate_height(height: float) -> bool:
    """Validate height range (cm)"""
    return 50 <= height <= 250


def validate_weight(weight: float) -> bool:
    """Validate weight range (kg)"""
    return 10 <= weight <= 300


def validate_assessment_score(score: Optional[int], min_score: int = 0, max_score: int = 100) -> bool:
    """Validate assessment score range"""
    if score is None:
        return True  # Optional field
    return min_score <= score <= max_score


def validate_time_duration(duration: Optional[float]) -> bool:
    """Validate time duration (seconds)"""
    if duration is None:
        return True  # Optional field
    return 0 <= duration <= 3600  # Max 1 hour


def validate_distance(distance: Optional[float]) -> bool:
    """Validate distance measurement"""
    if distance is None:
        return True  # Optional field
    return 0 <= distance <= 1000  # Max 1000 units


def validate_heart_rate(heart_rate: Optional[int]) -> bool:
    """Validate heart rate range"""
    if heart_rate is None:
        return True  # Optional field
    return 30 <= heart_rate <= 220  # Typical human range