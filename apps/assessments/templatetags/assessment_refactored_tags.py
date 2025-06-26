"""
Template tags for working with refactored assessment models.
"""
from django import template

register = template.Library()


@register.filter
def get_test_score(assessment, test_type):
    """
    Get score from related test model.
    
    Usage: {{ assessment|get_test_score:"overhead_squat" }}
    """
    test_map = {
        'overhead_squat': 'overhead_squat_test',
        'push_up': 'push_up_test',
        'balance': 'single_leg_balance_test',
        'toe_touch': 'toe_touch_test',
        'shoulder_mobility': 'shoulder_mobility_test',
        'farmers_carry': 'farmers_carry_test',
        'harvard_step': 'harvard_step_test'
    }
    
    test_attr = test_map.get(test_type)
    if not test_attr:
        return None
    
    try:
        test_obj = getattr(assessment, test_attr)
        if test_obj:
            if hasattr(test_obj, 'calculate_score'):
                return test_obj.calculate_score()
            elif hasattr(test_obj, 'score'):
                return test_obj.score
            elif hasattr(test_obj, 'score_manual'):
                return test_obj.score_manual
    except AttributeError:
        pass
    
    return None


@register.filter
def get_test_field(assessment, field_path):
    """
    Get specific field from related test model.
    
    Usage: {{ assessment|get_test_field:"overhead_squat_test.knee_valgus" }}
    """
    try:
        parts = field_path.split('.')
        obj = assessment
        
        for part in parts:
            obj = getattr(obj, part)
            if obj is None:
                return None
        
        return obj
    except (AttributeError, IndexError):
        return None


@register.simple_tag
def get_test_data(assessment, test_type):
    """
    Get all data from a test model as a dictionary.
    
    Usage: {% get_test_data assessment "overhead_squat" as squat_data %}
    """
    test_map = {
        'overhead_squat': 'overhead_squat_test',
        'push_up': 'push_up_test',
        'balance': 'single_leg_balance_test',
        'toe_touch': 'toe_touch_test',
        'shoulder_mobility': 'shoulder_mobility_test',
        'farmers_carry': 'farmers_carry_test',
        'harvard_step': 'harvard_step_test'
    }
    
    test_attr = test_map.get(test_type)
    if not test_attr:
        return {}
    
    try:
        test_obj = getattr(assessment, test_attr)
        if test_obj:
            # Convert model instance to dictionary
            data = {}
            for field in test_obj._meta.fields:
                if field.name not in ['id', 'assessment']:
                    data[field.name] = getattr(test_obj, field.name)
            
            # Add calculated score
            if hasattr(test_obj, 'calculate_score'):
                data['calculated_score'] = test_obj.calculate_score()
            
            return data
    except AttributeError:
        pass
    
    return {}


@register.inclusion_tag('assessments/components/test_display.html')
def display_test_results(assessment, test_type):
    """
    Display test results using a component template.
    
    Usage: {% display_test_results assessment "overhead_squat" %}
    """
    test_data = get_test_data(assessment, test_type)
    
    # Map test types to display names
    display_names = {
        'overhead_squat': '오버헤드 스쿼트',
        'push_up': '푸시업',
        'balance': '외발 균형',
        'toe_touch': '발가락 닿기',
        'shoulder_mobility': '어깨 가동성',
        'farmers_carry': '파머스 캐리',
        'harvard_step': '하버드 스텝 테스트'
    }
    
    return {
        'test_type': test_type,
        'test_name': display_names.get(test_type, test_type),
        'test_data': test_data,
        'has_data': bool(test_data)
    }


@register.filter
def has_test_data(assessment, test_type):
    """
    Check if assessment has data for specific test.
    
    Usage: {% if assessment|has_test_data:"overhead_squat" %}
    """
    test_map = {
        'overhead_squat': 'overhead_squat_test',
        'push_up': 'push_up_test',
        'balance': 'single_leg_balance_test',
        'toe_touch': 'toe_touch_test',
        'shoulder_mobility': 'shoulder_mobility_test',
        'farmers_carry': 'farmers_carry_test',
        'harvard_step': 'harvard_step_test'
    }
    
    test_attr = test_map.get(test_type)
    if not test_attr:
        return False
    
    try:
        return hasattr(assessment, test_attr) and getattr(assessment, test_attr) is not None
    except AttributeError:
        return False