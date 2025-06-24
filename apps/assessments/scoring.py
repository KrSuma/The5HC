# assessment_scoring.py - Functions for scoring and evaluating fitness tests with improved validation

from typing import Dict, Tuple, Any, Union, Optional
from django.core.cache import cache

# Scoring threshold constants
PUSHUP_THRESHOLDS = {
    'Male': {
        (0, 29): {'excellent': 36, 'good': 29, 'average': 22},
        (30, 39): {'excellent': 30, 'good': 24, 'average': 17},
        (40, 49): {'excellent': 25, 'good': 20, 'average': 13},
        (50, 59): {'excellent': 21, 'good': 16, 'average': 10},
        (60, 120): {'excellent': 18, 'good': 12, 'average': 8}
    },
    'Female': {
        (0, 29): {'excellent': 30, 'good': 21, 'average': 15},
        (30, 39): {'excellent': 27, 'good': 20, 'average': 13},
        (40, 49): {'excellent': 24, 'good': 15, 'average': 11},
        (50, 59): {'excellent': 21, 'good': 13, 'average': 9},
        (60, 120): {'excellent': 17, 'good': 12, 'average': 8}
    },
    '남성': {  # Korean for Male
        (0, 29): {'excellent': 36, 'good': 29, 'average': 22},
        (30, 39): {'excellent': 30, 'good': 24, 'average': 17},
        (40, 49): {'excellent': 25, 'good': 20, 'average': 13},
        (50, 59): {'excellent': 21, 'good': 16, 'average': 10},
        (60, 120): {'excellent': 18, 'good': 12, 'average': 8}
    },
    '여성': {  # Korean for Female
        (0, 29): {'excellent': 30, 'good': 21, 'average': 15},
        (30, 39): {'excellent': 27, 'good': 20, 'average': 13},
        (40, 49): {'excellent': 24, 'good': 15, 'average': 11},
        (50, 59): {'excellent': 21, 'good': 13, 'average': 9},
        (60, 120): {'excellent': 17, 'good': 12, 'average': 8}
    }
}

BALANCE_THRESHOLDS = {
    'open': {'excellent': 45, 'good': 30, 'average': 15},
    'closed': {'excellent': 30, 'good': 20, 'average': 10}
}

FARMERS_CARRY_THRESHOLDS = {
    'distance': {'excellent': 30, 'good': 20, 'average': 10},
    'time': {
        'Male': {'excellent': 60, 'good': 45, 'average': 30},
        'Female': {'excellent': 45, 'good': 30, 'average': 20},
        '남성': {'excellent': 60, 'good': 45, 'average': 30},
        '여성': {'excellent': 45, 'good': 30, 'average': 20}
    }
}

STEP_TEST_THRESHOLDS = {
    'pfi': {'excellent': 90, 'good': 80, 'average': 65}
}


def get_test_standard(test_type: str, gender: str = 'A', age: int = 30, 
                     variation_type: str = None, conditions: str = None):
    """
    Get test standard from database with caching and fallback to hardcoded values.
    
    Args:
        test_type: Type of test (push_up, farmer_carry, etc.)
        gender: Gender ('M', 'F', or 'A')
        age: Age in years
        variation_type: Optional variation type
        conditions: Optional conditions
        
    Returns:
        TestStandard instance or None
    """
    # Import here to avoid circular imports
    try:
        from .models import TestStandard
    except ImportError:
        return None
    
    # Create cache key
    cache_key = f"test_standard_{test_type}_{gender}_{age}_{variation_type}_{conditions}"
    
    # Try to get from cache first
    standard = cache.get(cache_key)
    if standard is not None:
        return standard
    
    # Get from database
    try:
        standard = TestStandard.get_standard(
            test_type=test_type,
            gender=gender,
            age=age,
            variation_type=variation_type,
            conditions=conditions
        )
        
        # Cache for 1 hour
        cache.set(cache_key, standard, 3600)
        return standard
        
    except Exception:
        # Database error or model not available - return None for fallback
        return None


def get_score_from_standard_or_fallback(test_type: str, value: float, gender: str = 'A', 
                                       age: int = 30, variation_type: str = None, 
                                       conditions: str = None) -> int:
    """
    Get score using database standard or fallback to hardcoded thresholds.
    
    Args:
        test_type: Type of test
        value: Test result value
        gender: Gender ('M', 'F', or 'A')
        age: Age in years
        variation_type: Optional variation type
        conditions: Optional conditions
        
    Returns:
        int: Score from 1-4
    """
    # Try to get from database first
    standard = get_test_standard(test_type, gender, age, variation_type, conditions)
    
    if standard:
        return standard.get_score_for_value(value)
    
    # Fallback to hardcoded values
    return _get_fallback_score(test_type, value, gender, age, variation_type, conditions)


def _get_fallback_score(test_type: str, value: float, gender: str = 'A', 
                       age: int = 30, variation_type: str = None, 
                       conditions: str = None) -> int:
    """
    Fallback scoring using hardcoded thresholds.
    """
    if test_type == 'push_up':
        return _fallback_pushup_score(gender, age, int(value), variation_type or 'standard')
    elif test_type == 'balance':
        return _fallback_balance_score(value, conditions or 'eyes_open')
    elif test_type == 'farmer_carry':
        return _fallback_farmers_carry_score(gender, value)
    elif test_type == 'step_test':
        return _fallback_step_test_score(value)
    else:
        # Generic fallback based on percentages
        if value >= 4:
            return 4
        elif value >= 3:
            return 3
        elif value >= 2:
            return 2
        else:
            return 1


def _fallback_pushup_score(gender: str, age: int, reps: int, push_up_type: str) -> int:
    """Fallback push-up scoring using hardcoded thresholds."""
    # Convert gender format
    gender_map = {'M': 'Male', 'F': 'Female', 'A': 'Male'}
    gender_key = gender_map.get(gender, gender)
    
    # Find age range
    age_range = None
    thresholds_dict = PUSHUP_THRESHOLDS.get(gender_key, PUSHUP_THRESHOLDS['Male'])
    
    for age_range_tuple in thresholds_dict:
        if age_range_tuple[0] <= age <= age_range_tuple[1]:
            age_range = age_range_tuple
            break
    
    if age_range is None:
        age_range = max(thresholds_dict.keys())
    
    thresholds = thresholds_dict[age_range]
    
    # Calculate base score
    if reps >= thresholds['excellent']:
        base_score = 4
    elif reps >= thresholds['good']:
        base_score = 3
    elif reps >= thresholds['average']:
        base_score = 2
    else:
        base_score = 1
    
    # Apply variation adjustments
    if push_up_type == 'modified':
        base_score = max(1, min(4, round(base_score * 0.7)))
    elif push_up_type == 'wall':
        base_score = max(1, min(4, round(base_score * 0.4)))
    
    return base_score


def _fallback_balance_score(time_seconds: float, conditions: str) -> int:
    """Fallback balance scoring using hardcoded thresholds."""
    if conditions == 'eyes_closed':
        thresholds = BALANCE_THRESHOLDS['closed']
    else:
        thresholds = BALANCE_THRESHOLDS['open']
    
    if time_seconds >= thresholds['excellent']:
        return 4
    elif time_seconds >= thresholds['good']:
        return 3
    elif time_seconds >= thresholds['average']:
        return 2
    else:
        return 1


def _fallback_farmers_carry_score(gender: str, time_seconds: float) -> int:
    """Fallback farmer's carry scoring using hardcoded thresholds."""
    gender_map = {'M': 'Male', 'F': 'Female', 'A': 'Male'}
    gender_key = gender_map.get(gender, gender)
    
    thresholds = FARMERS_CARRY_THRESHOLDS['time'].get(gender_key, 
                                                     FARMERS_CARRY_THRESHOLDS['time']['Male'])
    
    if time_seconds >= thresholds['excellent']:
        return 4
    elif time_seconds >= thresholds['good']:
        return 3
    elif time_seconds >= thresholds['average']:
        return 2
    else:
        return 1


def _fallback_step_test_score(pfi: float) -> int:
    """Fallback step test scoring using hardcoded thresholds."""
    thresholds = STEP_TEST_THRESHOLDS['pfi']
    
    if pfi >= thresholds['excellent']:
        return 4
    elif pfi >= thresholds['good']:
        return 3
    elif pfi >= thresholds['average']:
        return 2
    else:
        return 1


def get_score_description(score: float, max_score: float = 100) -> str:
    """
    Convert numerical score to descriptive rating
    
    Args:
        score: The score to convert
        max_score: The maximum possible score
        
    Returns:
        str: A description of the score
    """
    # Validate inputs
    score = max(0, min(max_score, float(score)))
    max_score = max(1, float(max_score))
    
    percentage = (score / max_score) * 100

    if percentage >= 90:
        return "Very Excellent"
    elif percentage >= 80:
        return "Excellent"
    elif percentage >= 70:
        return "Average"
    elif percentage >= 60:
        return "Needs Attention"
    else:
        return "Needs Improvement"


def calculate_overhead_squat_score(form_quality=None, knee_valgus=False, 
                                   forward_lean=False, heel_lift=False, pain=False):
    """
    Calculate score for overhead squat test with movement quality
    
    Args:
        form_quality: Quality of form (0-3) - for backward compatibility
        knee_valgus: Boolean - knees cave inward during squat
        forward_lean: Boolean - excessive forward lean
        heel_lift: Boolean - heels lift off ground
        pain: Boolean - pain during test
            
    Returns:
        int: Score from 0-3
    """
    if pain:
        return 0
    
    # If form_quality provided (backward compatibility)
    if form_quality is not None:
        return max(0, min(3, form_quality))
    
    # Calculate based on compensations
    compensations = sum([knee_valgus, forward_lean, heel_lift])
    
    if compensations == 0:
        return 3  # Perfect form
    elif compensations == 1:
        return 2  # Minor compensations
    elif compensations >= 2:
        return 1  # Major compensations
    
    return 1


def calculate_pushup_score(gender: str, age: int, reps: int, push_up_type: str = 'standard') -> int:
    """
    Calculate score for push-up test based on gender, age, repetitions, and type.
    Uses database standards with fallback to hardcoded values.
    
    Args:
        gender: 'Male'/'남성' or 'Female'/'여성'
        age: Age in years
        reps: Number of repetitions completed
        push_up_type: Type of push-up performed ('standard', 'modified', 'wall')
        
    Returns:
        int: Score from 1-4
    """
    # Validate inputs
    age = max(0, min(120, age))
    reps = max(0, reps)
    
    # Convert gender to database format
    gender_map = {
        'Male': 'M', 'Female': 'F', '남성': 'M', '여성': 'F'
    }
    db_gender = gender_map.get(gender, 'M')
    
    # Try to get score from database standard first
    try:
        score = get_score_from_standard_or_fallback(
            test_type='push_up',
            value=reps,
            gender=db_gender,
            age=age,
            variation_type=push_up_type
        )
        return score
    except Exception:
        # Fallback to original logic if database fails
        return _fallback_pushup_score(db_gender, age, reps, push_up_type)


def calculate_single_leg_balance_score(right_open: int, left_open: int, right_closed: int, left_closed: int) -> float:
    """
    Calculate single leg balance score based on time in seconds.
    Uses database standards with fallback to hardcoded values.
    
    Args:
        right_open: Time in seconds for right leg with eyes open
        left_open: Time in seconds for left leg with eyes open
        right_closed: Time in seconds for right leg with eyes closed
        left_closed: Time in seconds for left leg with eyes closed
        
    Returns:
        float: Score from 1.0-4.0
    """
    # Validate inputs
    right_open = max(0, min(120, right_open))
    left_open = max(0, min(120, left_open))
    right_closed = max(0, min(120, right_closed))
    left_closed = max(0, min(120, left_closed))

    # Average the times for each condition
    open_eyes_avg = (right_open + left_open) / 2
    closed_eyes_avg = (right_closed + left_closed) / 2

    try:
        # Score for eyes open using database standards
        open_score = get_score_from_standard_or_fallback(
            test_type='balance',
            value=open_eyes_avg,
            gender='A',  # Balance standards are generally gender-neutral
            age=30,
            conditions='eyes_open'
        )
        
        # Score for eyes closed using database standards
        closed_score = get_score_from_standard_or_fallback(
            test_type='balance',
            value=closed_eyes_avg,
            gender='A',
            age=30,
            conditions='eyes_closed'
        )
        
        # Combined score (weighted slightly towards the more challenging eyes-closed test)
        return (float(open_score) * 0.4) + (float(closed_score) * 0.6)
        
    except Exception:
        # Fallback to original logic if database fails
        return _fallback_balance_combined_score(open_eyes_avg, closed_eyes_avg)


def _fallback_balance_combined_score(open_eyes_avg: float, closed_eyes_avg: float) -> float:
    """Fallback balance scoring using original logic."""
    # Score for eyes open
    if open_eyes_avg >= BALANCE_THRESHOLDS['open']['excellent']:
        open_score = 4  # Excellent
    elif open_eyes_avg >= BALANCE_THRESHOLDS['open']['good']:
        open_score = 3  # Good
    elif open_eyes_avg >= BALANCE_THRESHOLDS['open']['average']:
        open_score = 2  # Average
    else:
        open_score = 1  # Needs improvement

    # Score for eyes closed
    if closed_eyes_avg >= BALANCE_THRESHOLDS['closed']['excellent']:
        closed_score = 4  # Excellent
    elif closed_eyes_avg >= BALANCE_THRESHOLDS['closed']['good']:
        closed_score = 3  # Good
    elif closed_eyes_avg >= BALANCE_THRESHOLDS['closed']['average']:
        closed_score = 2  # Average
    else:
        closed_score = 1  # Needs improvement

    # Combined score (weighted slightly towards the more challenging eyes-closed test)
    return (open_score * 0.4) + (closed_score * 0.6)


def calculate_toe_touch_score(distance: float) -> int:
    """
    Calculate toe touch score based on distance in cm
    
    Args:
        distance: Distance in cm (positive is past the floor, negative is above the floor)
        
    Returns:
        int: Score from 1-4
    """
    distance = float(distance)  # Ensure it's a float
    
    if distance >= 5:  # +5cm (past the floor)
        return 4  # Excellent
    elif distance >= 0:  # 0 to +5cm (touching floor)
        return 3  # Good
    elif distance >= -10:  # -10cm to 0cm (ankle level)
        return 2  # Average
    else:  # Less than -10cm
        return 1  # Needs improvement


def calculate_shoulder_mobility_score(fist_distance: int) -> int:
    """
    Calculate shoulder mobility score based on FMS criteria
    
    Args:
        fist_distance: FMS score value (0-3)
            3 - Fists within 1 fist distance
            2 - Fists within 1.5 fist distance
            1 - Fists beyond 2 fist distances
            0 - Pain during clearing test
            
    Returns:
        int: Score from 0-3
    """
    # Validate input
    return max(0, min(3, fist_distance))


def calculate_farmers_carry_score(gender: str, weight: float, distance: float, time: int, body_weight_percentage: float = None) -> float:
    """
    Calculate Farmer's Carry score based on distance, time, and form.
    Uses database standards with fallback to hardcoded values.
    
    Args:
        gender: 'Male'/'남성' or 'Female'/'여성'
        weight: Weight carried in kg
        distance: Distance carried in meters
        time: Time carrying the weight in seconds
        body_weight_percentage: Percentage of body weight used (optional)
        
    Returns:
        float: Score from 1.0-4.0
    """
    # Validate inputs
    weight = max(0, weight)
    distance = max(0, distance)
    time = max(0, time)
    
    # Convert gender to database format
    gender_map = {
        'Male': 'M', 'Female': 'F', '남성': 'M', '여성': 'F'
    }
    db_gender = gender_map.get(gender, 'M')
    
    # Try to get score from database standard first (using time as primary metric)
    try:
        time_score = get_score_from_standard_or_fallback(
            test_type='farmer_carry',
            value=time,
            gender=db_gender,
            age=30  # Default age since farmer carry standards are generally age-independent
        )
        
        # Convert to float score
        base_score = float(time_score)
        
        # Apply body weight percentage adjustment if provided
        if body_weight_percentage is not None and body_weight_percentage > 0:
            # Apply variation scoring for different weights
            if body_weight_percentage < 50:
                # Lighter weight - reduce score
                adjustment = body_weight_percentage / 50
                base_score = base_score * max(0.5, adjustment)
            elif body_weight_percentage > 100:
                # Heavier weight - increase score (up to 20% bonus)
                adjustment = min(1.2, 1 + (body_weight_percentage - 100) / 500)
                base_score = base_score * adjustment
        
        return max(1.0, min(4.0, base_score))
        
    except Exception:
        # Fallback to original logic if database fails
        return _fallback_farmers_carry_combined_score(gender, distance, time, body_weight_percentage)


def _fallback_farmers_carry_combined_score(gender: str, distance: float, time: int, body_weight_percentage: float = None) -> float:
    """Fallback farmer's carry scoring using original logic."""
    # Score based on distance
    if distance >= FARMERS_CARRY_THRESHOLDS['distance']['excellent']:
        distance_score = 4  # Excellent
    elif distance >= FARMERS_CARRY_THRESHOLDS['distance']['good']:
        distance_score = 3  # Good
    elif distance >= FARMERS_CARRY_THRESHOLDS['distance']['average']:
        distance_score = 2  # Average
    else:
        distance_score = 1  # Needs improvement

    # Score based on time
    gender_thresholds = FARMERS_CARRY_THRESHOLDS['time'].get(gender, FARMERS_CARRY_THRESHOLDS['time']['Male'])
    
    if time >= gender_thresholds['excellent']:
        time_score = 4  # Excellent
    elif time >= gender_thresholds['good']:
        time_score = 3  # Good
    elif time >= gender_thresholds['average']:
        time_score = 2  # Average
    else:
        time_score = 1  # Needs improvement

    # Combined score
    base_score = (distance_score + time_score) / 2
    
    # Apply adjustment based on body weight percentage if provided
    if body_weight_percentage is not None and body_weight_percentage > 0:
        # Normalize score based on body weight percentage
        # Standard is 50% body weight for males, 40% for females
        standard_percentage = 50 if gender in ['Male', '남성'] else 40
        
        # Calculate adjustment factor (higher percentage = harder = higher score)
        adjustment_factor = body_weight_percentage / standard_percentage
        
        # Apply adjustment with reasonable limits (0.5x to 1.5x)
        adjusted_score = base_score * max(0.5, min(1.5, adjustment_factor))
        
        return max(1.0, min(4.0, adjusted_score))
    
    return base_score


def calculate_step_test_score(hr1: int, hr2: int, hr3: int) -> Tuple[int, float]:
    """
    Calculate Harvard Step Test score based on recovery heart rates
    
    Args:
        hr1: Heart rate 1-1.5 minutes after exercise (bpm)
        hr2: Heart rate 2-2.5 minutes after exercise (bpm)
        hr3: Heart rate 3-3.5 minutes after exercise (bpm)
        
    Returns:
        Tuple[int, float]: (Score from 1-4, Physical Fitness Index)
    """
    # Validate inputs
    hr1 = max(40, min(220, hr1))
    hr2 = max(40, min(220, hr2))
    hr3 = max(40, min(220, hr3))

    # Physical Fitness Index (PFI)
    test_duration = 180  # 3 minutes in seconds
    pfi = (100 * test_duration) / (2 * (hr1 + hr2 + hr3))

    # Score based on PFI
    if pfi >= STEP_TEST_THRESHOLDS['pfi']['excellent']:
        return 4, pfi  # Excellent
    elif pfi >= STEP_TEST_THRESHOLDS['pfi']['good']:
        return 3, pfi  # Good
    elif pfi >= STEP_TEST_THRESHOLDS['pfi']['average']:
        return 2, pfi  # Average
    else:
        return 1, pfi  # Needs improvement


def calculate_category_scores(assessment_data: Dict[str, Any], client_details: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate category scores (strength, mobility, balance, cardio)
    
    Args:
        assessment_data: Dictionary containing assessment values
        client_details: Dictionary containing client information
        
    Returns:
        Dict[str, float]: Dictionary containing category scores
    """
    # Get client gender and age for age/gender-specific scoring
    gender = client_details['gender']
    age = client_details['age']

    # Strength score (30% of total) - Push-up and Farmer's Carry
    push_up_score = float(assessment_data.get('push_up_score', 1))
    farmers_carry_score = float(assessment_data.get('farmers_carry_score', 1))

    strength_score = (push_up_score + farmers_carry_score) / 2 * 25

    # Mobility score (25% of total) - Toe Touch and Shoulder Mobility
    toe_touch_score = float(assessment_data.get('toe_touch_score', 1))
    shoulder_mobility_score = float(assessment_data.get('shoulder_mobility_score', 1))

    # Convert shoulder_mobility_score from 0-5 scale to 1-4 scale for consistency
    # Note: Score 0 maps to 1, Score 5 maps to 4
    if shoulder_mobility_score == 0:
        shoulder_mobility_normalized = 1
    else:
        # Map 1-5 to 1.6-4 range
        shoulder_mobility_normalized = 1 + (shoulder_mobility_score - 1) * 0.6

    mobility_score = (toe_touch_score + shoulder_mobility_normalized) / 2 * 25

    # Balance score (25% of total) - Single Leg Balance and Overhead Squat
    single_leg_balance_score = calculate_single_leg_balance_score(
        assessment_data.get('single_leg_balance_right_open', 0),
        assessment_data.get('single_leg_balance_left_open', 0),
        assessment_data.get('single_leg_balance_right_closed', 0),
        assessment_data.get('single_leg_balance_left_closed', 0)
    )
    
    overhead_squat_score = float(assessment_data.get('overhead_squat_score', 1))
    # Convert overhead_squat_score from 0-5 scale to 1-4 scale for consistency
    # Note: Score 0 maps to 1, Score 5 maps to 4
    if overhead_squat_score == 0:
        overhead_squat_normalized = 1
    else:
        # Map 1-5 to 1.6-4 range
        overhead_squat_normalized = 1 + (overhead_squat_score - 1) * 0.6

    balance_score = (single_leg_balance_score + overhead_squat_normalized) / 2 * 25

    # Cardio score (20% of total) - Harvard Step Test
    step_test_score, pfi = calculate_step_test_score(
        assessment_data.get('step_test_hr1', 90),
        assessment_data.get('step_test_hr2', 80),
        assessment_data.get('step_test_hr3', 70)
    )

    cardio_score = step_test_score * 20

    # Overall score (weighted by importance)
    overall_score = (
        strength_score * 0.3 + 
        mobility_score * 0.25 + 
        balance_score * 0.25 + 
        cardio_score * 0.2
    )

    return {
        'overall_score': overall_score,
        'strength_score': strength_score,
        'mobility_score': mobility_score,
        'balance_score': balance_score,
        'cardio_score': cardio_score,
        'pfi': pfi  # Return PFI for display
    }


def apply_temperature_adjustment(score: float, temperature: float, test_environment: str) -> float:
    """
    Apply temperature adjustment to test scores for outdoor testing.
    
    Args:
        score: Base score to adjust
        temperature: Temperature in Celsius
        test_environment: 'indoor' or 'outdoor'
        
    Returns:
        float: Adjusted score
    """
    if test_environment != 'outdoor' or temperature is None:
        return score
    
    # Optimal temperature range is 15-25°C
    if 15 <= temperature <= 25:
        return score  # No adjustment needed
    
    # Calculate adjustment based on temperature deviation
    if temperature < 15:
        # Cold weather adjustment (harder conditions)
        deviation = 15 - temperature
        # Max 10% bonus for extreme cold (< 5°C)
        adjustment_factor = 1 + min(0.1, deviation * 0.01)
    else:  # temperature > 25
        # Hot weather adjustment (harder conditions)
        deviation = temperature - 25
        # Max 10% bonus for extreme heat (> 35°C)
        adjustment_factor = 1 + min(0.1, deviation * 0.01)
    
    return min(score * adjustment_factor, 100)  # Cap at max score


def calculate_scores(client, assessment_data):
    """
    Calculate scores for an assessment using the client and assessment data.
    
    Args:
        client: Client object with gender, age, etc.
        assessment_data: Dictionary containing assessment test results
        
    Returns:
        Dictionary with calculated scores
    """
    client_details = {
        'gender': client.gender,
        'age': client.age
    }
    
    return calculate_category_scores(assessment_data, client_details)