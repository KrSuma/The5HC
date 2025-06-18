"""
Korean translations for risk calculator primary concerns
"""

def get_korean_primary_concerns(risk_factors):
    """
    Extract primary concerns from risk factors in Korean.
    
    Args:
        risk_factors: Dictionary of identified risk factors
        
    Returns:
        List of primary concern descriptions in Korean
    """
    concerns = []
    
    # Check category imbalance
    if risk_factors.get('category_imbalance'):
        worst_category = max(
            risk_factors['category_imbalance'].items(),
            key=lambda x: x[1].get('deviation', 0)
        )
        category_name = worst_category[0]
        # Handle both uppercase and lowercase category names
        if category_name.lower() == 'strength':
            category_korean = '근력'
        elif category_name.lower() == 'mobility':
            category_korean = '유연성'
        elif category_name.lower() == 'balance':
            category_korean = '균형'
        elif category_name.lower() == 'cardio':
            category_korean = '심폐지구력'
        else:
            category_korean = category_name
            
        concerns.append(f"심각한 {category_korean} 불균형 ({worst_category[1]['percentage']}% 편차)")
    
    # Check bilateral asymmetry
    if risk_factors.get('bilateral_asymmetry'):
        if 'shoulder_mobility' in risk_factors['bilateral_asymmetry']:
            concerns.append(f"어깨 가동성 비대칭 ({risk_factors['bilateral_asymmetry']['shoulder_mobility']['difference_cm']}cm)")
        if 'balance_eyes_open' in risk_factors['bilateral_asymmetry']:
            concerns.append(f"균형 비대칭 ({risk_factors['bilateral_asymmetry']['balance_eyes_open']['asymmetry_percentage']}%)")
    
    # Check movement compensations
    if risk_factors.get('movement_compensations'):
        if isinstance(risk_factors['movement_compensations'], dict) and 'overhead_squat' in risk_factors['movement_compensations']:
            count = risk_factors['movement_compensations']['count']
            concerns.append(f"움직임 보상 (오버헤드 스쿼트에서 {count}개 문제)")
    
    # Check poor mobility
    if risk_factors.get('poor_mobility'):
        concerns.append(f"{len(risk_factors['poor_mobility'])}개 테스트에서 낮은 유연성")
    
    # Check poor balance
    if risk_factors.get('poor_balance'):
        for balance_issue in risk_factors['poor_balance']:
            if 'interpretation' in balance_issue:
                if 'poor balance' in balance_issue['interpretation']:
                    concerns.append("낮은 균형 능력")
                    break
    
    return concerns[:3]  # Return top 3 concerns