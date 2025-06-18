"""
Risk calculation module for injury risk assessment.
Analyzes assessment data to identify injury risk factors and calculate overall risk score.
"""
from typing import Dict, List, Optional, Tuple
import json


def calculate_injury_risk(assessment_data: Dict) -> Tuple[float, Dict]:
    """
    Calculate injury risk score based on assessment data patterns.
    
    Args:
        assessment_data: Dictionary containing assessment scores and measurements
        
    Returns:
        Tuple of (risk_score: float, risk_factors: dict)
        - risk_score: 0-100 scale (0=low risk, 100=high risk)
        - risk_factors: Detailed analysis of identified risks
    """
    risk_factors = {
        'category_imbalance': {},
        'bilateral_asymmetry': {},
        'poor_mobility': [],
        'poor_balance': [],
        'movement_compensations': [],
        'low_strength': [],
        'poor_cardio': [],
        'overall_risk_level': 'low'
    }
    
    total_risk_score = 0.0
    risk_count = 0
    
    # 1. Check Category Imbalance (30% weight)
    category_scores = {
        'strength': assessment_data.get('strength_score', 0),
        'mobility': assessment_data.get('mobility_score', 0),
        'balance': assessment_data.get('balance_score', 0),
        'cardio': assessment_data.get('cardio_score', 0)
    }
    
    if all(score > 0 for score in category_scores.values()):
        avg_score = sum(category_scores.values()) / len(category_scores)
        max_deviation = 0
        
        for category, score in category_scores.items():
            deviation = abs(score - avg_score)
            if deviation > max_deviation:
                max_deviation = deviation
            
            # Flag significant imbalances (>30% deviation from average)
            if deviation > avg_score * 0.3:
                risk_factors['category_imbalance'][category] = {
                    'score': score,
                    'average': round(avg_score, 1),
                    'deviation': round(deviation, 1),
                    'percentage': round((deviation / avg_score) * 100, 1)
                }
        
        # Calculate imbalance risk (0-30 points)
        imbalance_risk = min(30, (max_deviation / avg_score) * 50)
        total_risk_score += imbalance_risk
        risk_count += 1
    
    # 2. Check Bilateral Asymmetry (20% weight)
    # Single leg balance asymmetry
    right_open = assessment_data.get('single_leg_balance_right_eyes_open', 0)
    left_open = assessment_data.get('single_leg_balance_left_eyes_open', 0)
    right_closed = assessment_data.get('single_leg_balance_right_eyes_closed', 0)
    left_closed = assessment_data.get('single_leg_balance_left_eyes_closed', 0)
    
    if right_open > 0 and left_open > 0:
        open_asymmetry = abs(right_open - left_open) / max(right_open, left_open) * 100
        if open_asymmetry > 30:  # >30% difference is concerning
            risk_factors['bilateral_asymmetry']['balance_eyes_open'] = {
                'right': right_open,
                'left': left_open,
                'asymmetry_percentage': round(open_asymmetry, 1)
            }
            asymmetry_risk = min(20, open_asymmetry * 0.4)
            total_risk_score += asymmetry_risk
            risk_count += 1
    
    if right_closed > 0 and left_closed > 0:
        closed_asymmetry = abs(right_closed - left_closed) / max(right_closed, left_closed) * 100
        if closed_asymmetry > 30:
            risk_factors['bilateral_asymmetry']['balance_eyes_closed'] = {
                'right': right_closed,
                'left': left_closed,
                'asymmetry_percentage': round(closed_asymmetry, 1)
            }
            asymmetry_risk = min(20, closed_asymmetry * 0.4)
            total_risk_score += asymmetry_risk
            risk_count += 1
    
    # Shoulder mobility asymmetry
    shoulder_asymmetry = assessment_data.get('shoulder_mobility_asymmetry', 0)
    if shoulder_asymmetry and shoulder_asymmetry > 2:  # >2cm difference
        risk_factors['bilateral_asymmetry']['shoulder_mobility'] = {
            'difference_cm': shoulder_asymmetry,
            'risk_level': 'high' if shoulder_asymmetry > 5 else 'moderate'
        }
        asymmetry_risk = min(20, shoulder_asymmetry * 3)
        total_risk_score += asymmetry_risk
        risk_count += 1
    
    # 3. Check Poor Mobility Indicators (15% weight)
    mobility_tests = {
        'overhead_squat': assessment_data.get('overhead_squat_score', 3),
        'toe_touch': assessment_data.get('toe_touch_score', 3),
        'shoulder_mobility': assessment_data.get('shoulder_mobility_score', 3)
    }
    
    for test, score in mobility_tests.items():
        if score is not None and score <= 1:  # Score of 0 or 1 indicates poor mobility
            risk_factors['poor_mobility'].append({
                'test': test,
                'score': score,
                'interpretation': 'severe limitation' if score == 0 else 'significant limitation'
            })
            mobility_risk = 15 if score == 0 else 10
            total_risk_score += mobility_risk
            risk_count += 1
    
    # 4. Check Poor Balance Indicators (15% weight)
    balance_score = assessment_data.get('balance_score', 0)
    if balance_score > 0 and balance_score < 40:  # Below 40% is concerning
        risk_factors['poor_balance'].append({
            'balance_score': balance_score,
            'interpretation': 'high fall risk' if balance_score < 20 else 'moderate fall risk'
        })
        balance_risk = 15 * (1 - balance_score / 100)
        total_risk_score += balance_risk
        risk_count += 1
    
    # Check specific balance tests
    if right_open < 10 or left_open < 10:  # Less than 10 seconds is poor
        risk_factors['poor_balance'].append({
            'test': 'single_leg_eyes_open',
            'duration': min(right_open, left_open),
            'interpretation': 'poor static balance'
        })
        total_risk_score += 10
        risk_count += 1
    
    # 5. Check Movement Compensations (10% weight)
    compensations = []
    if assessment_data.get('overhead_squat_knee_valgus'):
        compensations.append('knee valgus')
    if assessment_data.get('overhead_squat_forward_lean'):
        compensations.append('forward lean')
    if assessment_data.get('overhead_squat_heel_lift'):
        compensations.append('heel lift')
    
    if compensations:
        risk_factors['movement_compensations'] = {
            'overhead_squat': compensations,
            'count': len(compensations),
            'risk_level': 'high' if len(compensations) >= 2 else 'moderate'
        }
        compensation_risk = min(10, len(compensations) * 4)
        total_risk_score += compensation_risk
        risk_count += 1
    
    # Pain indicators
    if assessment_data.get('shoulder_mobility_pain'):
        if not isinstance(risk_factors['movement_compensations'], list):
            if 'pain_indicators' not in risk_factors['movement_compensations']:
                risk_factors['movement_compensations']['pain_indicators'] = []
            risk_factors['movement_compensations']['pain_indicators'].append({
                'test': 'shoulder_mobility',
                'issue': 'pain during clearing test',
                'risk_level': 'high'
            })
        total_risk_score += 10
        risk_count += 1
    
    # 6. Check Low Strength Indicators (5% weight)
    strength_score = assessment_data.get('strength_score', 0)
    if strength_score > 0 and strength_score < 30:  # Below 30% is concerning
        risk_factors['low_strength'].append({
            'strength_score': strength_score,
            'interpretation': 'severe weakness' if strength_score < 20 else 'significant weakness'
        })
        strength_risk = 5 * (1 - strength_score / 100)
        total_risk_score += strength_risk
        risk_count += 1
    
    # Specific strength tests
    push_up_score = assessment_data.get('push_up_score', 3)
    if push_up_score is not None and push_up_score <= 1:
        risk_factors['low_strength'].append({
            'test': 'push_up',
            'score': push_up_score,
            'interpretation': 'poor upper body strength'
        })
        total_risk_score += 5
        risk_count += 1
    
    # 7. Check Poor Cardio Indicators (5% weight)
    cardio_score = assessment_data.get('cardio_score', 0)
    if cardio_score > 0 and cardio_score < 30:  # Below 30% is concerning
        risk_factors['poor_cardio'].append({
            'cardio_score': cardio_score,
            'interpretation': 'poor cardiovascular fitness'
        })
        cardio_risk = 5 * (1 - cardio_score / 100)
        total_risk_score += cardio_risk
        risk_count += 1
    
    # Calculate final risk score (normalize to 0-100)
    if risk_count > 0:
        # Average the risks but cap at 100
        final_risk_score = min(100, total_risk_score)
    else:
        final_risk_score = 0
    
    # Determine overall risk level
    if final_risk_score >= 70:
        risk_factors['overall_risk_level'] = 'high'
    elif final_risk_score >= 40:
        risk_factors['overall_risk_level'] = 'moderate'
    elif final_risk_score >= 20:
        risk_factors['overall_risk_level'] = 'low-moderate'
    else:
        risk_factors['overall_risk_level'] = 'low'
    
    # Add summary
    risk_factors['summary'] = {
        'total_risk_score': round(final_risk_score, 1),
        'risk_count': risk_count,
        'primary_concerns': _get_primary_concerns(risk_factors)
    }
    
    return round(final_risk_score, 1), risk_factors


def _get_primary_concerns(risk_factors: Dict) -> List[str]:
    """
    Extract primary concerns from risk factors for summary.
    
    Args:
        risk_factors: Dictionary of identified risk factors
        
    Returns:
        List of primary concern descriptions
    """
    concerns = []
    
    # Check category imbalance
    if risk_factors.get('category_imbalance'):
        worst_category = max(
            risk_factors['category_imbalance'].items(),
            key=lambda x: x[1].get('deviation', 0)
        )
        concerns.append(f"Significant {worst_category[0]} imbalance ({worst_category[1]['percentage']}% deviation)")
    
    # Check bilateral asymmetry
    if risk_factors.get('bilateral_asymmetry'):
        if 'shoulder_mobility' in risk_factors['bilateral_asymmetry']:
            concerns.append(f"Shoulder mobility asymmetry ({risk_factors['bilateral_asymmetry']['shoulder_mobility']['difference_cm']}cm)")
        if 'balance_eyes_open' in risk_factors['bilateral_asymmetry']:
            concerns.append(f"Balance asymmetry ({risk_factors['bilateral_asymmetry']['balance_eyes_open']['asymmetry_percentage']}%)")
    
    # Check movement compensations
    if risk_factors.get('movement_compensations'):
        if isinstance(risk_factors['movement_compensations'], dict) and 'overhead_squat' in risk_factors['movement_compensations']:
            count = risk_factors['movement_compensations']['count']
            concerns.append(f"Movement compensations ({count} issues in overhead squat)")
    
    # Check poor mobility
    if risk_factors.get('poor_mobility'):
        concerns.append(f"Poor mobility in {len(risk_factors['poor_mobility'])} tests")
    
    # Check poor balance
    if risk_factors.get('poor_balance'):
        for balance_issue in risk_factors['poor_balance']:
            if 'interpretation' in balance_issue:
                concerns.append(balance_issue['interpretation'].title())
                break
    
    return concerns[:3]  # Return top 3 concerns


def interpret_risk_score(risk_score: float) -> Dict[str, str]:
    """
    Provide interpretation and recommendations based on risk score.
    
    Args:
        risk_score: Injury risk score (0-100)
        
    Returns:
        Dictionary with interpretation and recommendations
    """
    if risk_score >= 70:
        return {
            'level': 'High Risk',
            'color': 'red',
            'interpretation': 'Significant injury risk factors identified. Immediate intervention recommended.',
            'recommendations': [
                'Prioritize corrective exercises for identified weaknesses',
                'Consider referral to physical therapist or medical professional',
                'Avoid high-intensity activities until imbalances are addressed',
                'Focus on mobility and stability work',
                'Re-assess in 4-6 weeks'
            ]
        }
    elif risk_score >= 40:
        return {
            'level': 'Moderate Risk',
            'color': 'orange',
            'interpretation': 'Multiple risk factors present. Targeted intervention advised.',
            'recommendations': [
                'Implement corrective exercise program',
                'Address muscle imbalances and asymmetries',
                'Gradually progress exercise intensity',
                'Focus on identified weak areas',
                'Re-assess in 6-8 weeks'
            ]
        }
    elif risk_score >= 20:
        return {
            'level': 'Low-Moderate Risk',
            'color': 'yellow',
            'interpretation': 'Some risk factors identified. Preventive measures recommended.',
            'recommendations': [
                'Include injury prevention exercises in routine',
                'Monitor and address minor imbalances',
                'Maintain balanced training program',
                'Continue regular assessments',
                'Progress training as appropriate'
            ]
        }
    else:
        return {
            'level': 'Low Risk',
            'color': 'green',
            'interpretation': 'Minimal injury risk factors. Continue current training approach.',
            'recommendations': [
                'Maintain current fitness program',
                'Continue balanced training approach',
                'Regular assessments every 3-6 months',
                'Progress training intensity as tolerated',
                'Focus on performance goals'
            ]
        }