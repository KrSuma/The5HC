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
        return "매우 우수"  # Very Excellent
    elif percentage >= 80:
        return "우수"  # Excellent
    elif percentage >= 70:
        return "보통"  # Average
    elif percentage >= 60:
        return "주의 필요"  # Needs Attention
    else:
        return "개선 필요"  # Needs Improvement# assessment_scoring.py - Functions for scoring and evaluating fitness tests with improved validation

from typing import Dict, Tuple, Any, Union, Optional

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


def calculate_overhead_squat_score(form_quality: int) -> int:
    """
    Calculate score for overhead squat test
    
    Args:
        form_quality: Quality of form (0-3)
            3 - Perfect form
            2 - Compensatory movements
            1 - Unable to perform deep squat
            0 - Pain reported
            
    Returns:
        int: Score from 0-3
    """
    # Validate input
    form_quality = max(0, min(3, form_quality))
    return form_quality


def calculate_pushup_score(gender: str, age: int, reps: int) -> int:
    """
    Calculate score for push-up test based on gender, age and repetitions
    
    Args:
        gender: 'Male'/'남성' or 'Female'/'여성'
        age: Age in years
        reps: Number of repetitions completed
        
    Returns:
        int: Score from 1-4
    """
    # Validate inputs
    age = max(0, min(120, age))
    reps = max(0, reps)

    # Find the appropriate age range
    age_range = None
    for age_range_tuple in PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male']):
        if age_range_tuple[0] <= age <= age_range_tuple[1]:
            age_range = age_range_tuple
            break
    
    if age_range is None:
        # Fallback to the highest age range if not found
        age_range = max(PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male']).keys())

    # Get thresholds for the age range
    thresholds = PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male'])[age_range]
    
    # Calculate score
    if reps >= thresholds['excellent']:
        return 4  # Excellent
    elif reps >= thresholds['good']:
        return 3  # Good
    elif reps >= thresholds['average']:
        return 2  # Average
    else:
        return 1  # Needs improvement


def calculate_single_leg_balance_score(right_open: int, left_open: int, right_closed: int, left_closed: int) -> float:
    """
    Calculate single leg balance score based on time in seconds
    
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


def calculate_farmers_carry_score(gender: str, weight: float, distance: float, time: int) -> float:
    """
    Calculate Farmer's Carry score based on distance, time, and form
    
    Args:
        gender: 'Male'/'남성' or 'Female'/'여성'
        weight: Weight carried in kg
        distance: Distance carried in meters
        time: Time carrying the weight in seconds
        
    Returns:
        float: Score from 1.0-4.0
    """
    # Validate inputs
    weight = max(0, weight)
    distance = max(0, distance)
    time = max(0, time)

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
    return (distance_score + time_score) / 2


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

    # Convert shoulder_mobility_score from 0-3 scale to 1-4 scale for consistency
    shoulder_mobility_normalized = (shoulder_mobility_score / 3) * 4

    mobility_score = (toe_touch_score + shoulder_mobility_normalized) / 2 * 25

    # Balance score (25% of total) - Single Leg Balance and Overhead Squat
    single_leg_balance_score = calculate_single_leg_balance_score(
        assessment_data.get('single_leg_balance_right_open', 0),
        assessment_data.get('single_leg_balance_left_open', 0),
        assessment_data.get('single_leg_balance_right_closed', 0),
        assessment_data.get('single_leg_balance_left_closed', 0)
    )
    
    overhead_squat_score = float(assessment_data.get('overhead_squat_score', 1))
    # Convert overhead_squat_score from 0-3 scale to 1-4 scale for consistency
    overhead_squat_normalized = (overhead_squat_score / 3) * 4

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