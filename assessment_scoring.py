# assessment_scoring.py - Functions for scoring and evaluating fitness tests

def calculate_overhead_squat_score(form_quality):
    """
    Calculate score for overhead squat test
    3 - Perfect form
    2 - Compensatory movements
    1 - Unable to perform deep squat
    0 - Pain reported
    """
    return form_quality


def calculate_pushup_score(gender, age, reps):
    """Calculate score for push-up test based on gender, age and repetitions"""
    if gender == 'Male' or gender == '남성':
        if age < 30:
            if reps >= 36:
                return 4  # Excellent
            elif reps >= 29:
                return 3  # Good
            elif reps >= 22:
                return 2  # Average
            else:
                return 1  # Needs improvement
        elif age < 40:
            if reps >= 30:
                return 4
            elif reps >= 24:
                return 3
            elif reps >= 17:
                return 2
            else:
                return 1
        elif age < 50:
            if reps >= 25:
                return 4
            elif reps >= 20:
                return 3
            elif reps >= 13:
                return 2
            else:
                return 1
        elif age < 60:
            if reps >= 21:
                return 4
            elif reps >= 16:
                return 3
            elif reps >= 10:
                return 2
            else:
                return 1
        else:  # 60+
            if reps >= 18:
                return 4
            elif reps >= 12:
                return 3
            elif reps >= 8:
                return 2
            else:
                return 1
    else:  # Female
        if age < 30:
            if reps >= 30:
                return 4
            elif reps >= 21:
                return 3
            elif reps >= 15:
                return 2
            else:
                return 1
        elif age < 40:
            if reps >= 27:
                return 4
            elif reps >= 20:
                return 3
            elif reps >= 13:
                return 2
            else:
                return 1
        elif age < 50:
            if reps >= 24:
                return 4
            elif reps >= 15:
                return 3
            elif reps >= 11:
                return 2
            else:
                return 1
        elif age < 60:
            if reps >= 21:
                return 4
            elif reps >= 13:
                return 3
            elif reps >= 9:
                return 2
            else:
                return 1
        else:  # 60+
            if reps >= 17:
                return 4
            elif reps >= 12:
                return 3
            elif reps >= 8:
                return 2
            else:
                return 1


def calculate_single_leg_balance_score(right_open, left_open, right_closed, left_closed):
    """Calculate single leg balance score based on time in seconds"""
    # Average the times for each condition
    open_eyes_avg = (right_open + left_open) / 2
    closed_eyes_avg = (right_closed + left_closed) / 2

    # Score for eyes open
    if open_eyes_avg >= 45:
        open_score = 4  # Excellent
    elif open_eyes_avg >= 30:
        open_score = 3  # Good
    elif open_eyes_avg >= 15:
        open_score = 2  # Average
    else:
        open_score = 1  # Needs improvement

    # Score for eyes closed
    if closed_eyes_avg >= 30:
        closed_score = 4  # Excellent
    elif closed_eyes_avg >= 20:
        closed_score = 3  # Good
    elif closed_eyes_avg >= 10:
        closed_score = 2  # Average
    else:
        closed_score = 1  # Needs improvement

    # Combined score (weighted slightly towards the more challenging eyes-closed test)
    return (open_score * 0.4) + (closed_score * 0.6)


def calculate_toe_touch_score(distance):
    """Calculate toe touch score based on distance in cm"""
    if distance >= 5:  # +5cm (past the floor)
        return 4  # Excellent
    elif distance >= 0:  # 0 to +5cm (touching floor)
        return 3  # Good
    elif distance >= -10:  # -10cm to 0cm (ankle level)
        return 2  # Average
    else:  # Less than -10cm
        return 1  # Needs improvement


def calculate_shoulder_mobility_score(fist_distance):
    """
    Calculate shoulder mobility score based on FMS criteria
    3 - Fists within 1 fist distance
    2 - Fists within 1.5 fist distance
    1 - Fists beyond 2 fist distances
    0 - Pain during clearing test
    """
    return fist_distance  # Assuming the input is already the score (0-3)


def calculate_farmers_carry_score(gender, weight, distance, time):
    """Calculate Farmer's Carry score based on distance and form"""
    # Convert weight to % of ideal weight if needed

    # Score based on distance
    if distance >= 30:
        distance_score = 4  # Excellent
    elif distance >= 20:
        distance_score = 3  # Good
    elif distance >= 10:
        distance_score = 2  # Average
    else:
        distance_score = 1  # Needs improvement

    # Score based on time (if applicable)
    if gender == 'Male' or gender == '남성':
        if time >= 60:
            time_score = 4  # Excellent
        elif time >= 45:
            time_score = 3  # Good
        elif time >= 30:
            time_score = 2  # Average
        else:
            time_score = 1  # Needs improvement
    else:  # Female
        if time >= 45:
            time_score = 4  # Excellent
        elif time >= 30:
            time_score = 3  # Good
        elif time >= 20:
            time_score = 2  # Average
        else:
            time_score = 1  # Needs improvement

    # Combined score
    return (distance_score + time_score) / 2


def calculate_step_test_score(hr1, hr2, hr3):
    """Calculate Harvard Step Test score based on recovery heart rates"""
    # Physical Fitness Index (PFI)
    test_duration = 180  # 3 minutes in seconds
    pfi = (100 * test_duration) / (2 * (hr1 + hr2 + hr3))

    # Score based on PFI
    if pfi >= 90:
        return 4, pfi  # Excellent
    elif pfi >= 80:
        return 3, pfi  # Good
    elif pfi >= 65:
        return 2, pfi  # Average
    else:
        return 1, pfi  # Needs improvement


def calculate_category_scores(assessment_data, client_details):
    """Calculate category scores (strength, mobility, balance, cardio)"""

    # Get client gender and age for age/gender-specific scoring
    gender = client_details['gender']
    age = client_details['age']

    # Strength score (30% of total) - Push-up and Farmer's Carry
    push_up_score = calculate_pushup_score(gender, age, assessment_data['push_up_reps'])
    farmers_carry_score = calculate_farmers_carry_score(
        gender,
        assessment_data['farmers_carry_weight'],
        assessment_data['farmers_carry_distance'],
        assessment_data['farmers_carry_time']
    )

    strength_score = (push_up_score + farmers_carry_score) / 2 * 25

    # Mobility score (25% of total) - Toe Touch and Shoulder Mobility
    toe_touch_score = calculate_toe_touch_score(assessment_data['toe_touch_distance'])
    shoulder_mobility_score = assessment_data['shoulder_mobility_score']  # Already a score

    mobility_score = (toe_touch_score + shoulder_mobility_score / 3 * 4) / 2 * 25

    # Balance score (25% of total) - Single Leg Balance and Overhead Squat
    single_leg_balance_score = calculate_single_leg_balance_score(
        assessment_data['single_leg_balance_right_open'],
        assessment_data['single_leg_balance_left_open'],
        assessment_data['single_leg_balance_right_closed'],
        assessment_data['single_leg_balance_left_closed']
    )
    overhead_squat_score = assessment_data['overhead_squat_score']  # Already a score (0-3)

    balance_score = (single_leg_balance_score + overhead_squat_score / 3 * 4) / 2 * 25

    # Cardio score (20% of total) - Harvard Step Test
    step_test_score, pfi = calculate_step_test_score(
        assessment_data['step_test_hr1'],
        assessment_data['step_test_hr2'],
        assessment_data['step_test_hr3']
    )

    cardio_score = step_test_score * 20

    # Overall score (100 points max)
    overall_score = strength_score * 0.3 + mobility_score * 0.25 + balance_score * 0.25 + cardio_score * 0.2

    return {
        'overall_score': overall_score,
        'strength_score': strength_score,
        'mobility_score': mobility_score,
        'balance_score': balance_score,
        'cardio_score': cardio_score,
        'pfi': pfi  # Return PFI for display
    }


def get_score_description(score, max_score = 100):
    """Convert numerical score to descriptive rating"""
    percentage = (score / max_score) * 100

    if percentage >= 90:
        return "매우 우수"
    elif percentage >= 80:
        return "우수"
    elif percentage >= 70:
        return "보통"
    elif percentage >= 60:
        return "주의 필요"
    else:
        return "개선 필요"