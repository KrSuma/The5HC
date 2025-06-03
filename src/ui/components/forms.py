"""
Reusable form components
"""
import streamlit as st
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ...core.models import Client
from ...core.constants import Gender
from ...utils.validators import validate_age, validate_height, validate_weight, validate_email, validate_phone_number


def render_client_form(client: Optional[Client] = None, key_prefix: str = "") -> Tuple[bool, Dict[str, Any]]:
    """Render client information form"""
    st.subheader("고객 정보" if not client else "고객 정보 수정")
    
    # Form fields
    name = st.text_input(
        "이름 *", 
        value=client.name if client else "",
        key=f"{key_prefix}client_name"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input(
            "나이 *", 
            min_value=1, 
            max_value=120, 
            value=client.age if client else 25,
            key=f"{key_prefix}client_age"
        )
    
    with col2:
        gender = st.selectbox(
            "성별 *",
            options=["male", "female"],
            format_func=lambda x: "남성" if x == "male" else "여성",
            index=0 if not client else (0 if client.gender == "male" else 1),
            key=f"{key_prefix}client_gender"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        height = st.number_input(
            "신장 (cm) *", 
            min_value=50.0, 
            max_value=250.0, 
            value=float(client.height) if client else 170.0,
            step=0.1,
            key=f"{key_prefix}client_height"
        )
    
    with col2:
        weight = st.number_input(
            "체중 (kg) *", 
            min_value=10.0, 
            max_value=300.0, 
            value=float(client.weight) if client else 70.0,
            step=0.1,
            key=f"{key_prefix}client_weight"
        )
    
    email = st.text_input(
        "이메일", 
        value=client.email if client else "",
        key=f"{key_prefix}client_email"
    )
    
    phone = st.text_input(
        "전화번호", 
        value=client.phone if client else "",
        placeholder="010-1234-5678",
        key=f"{key_prefix}client_phone"
    )
    
    # Validation
    valid = True
    errors = []
    
    if not name.strip():
        errors.append("이름은 필수입니다.")
        valid = False
    
    if not validate_age(age):
        errors.append("올바른 나이를 입력해주세요.")
        valid = False
    
    if not validate_height(height):
        errors.append("올바른 신장을 입력해주세요.")
        valid = False
    
    if not validate_weight(weight):
        errors.append("올바른 체중을 입력해주세요.")
        valid = False
    
    if email and not validate_email(email):
        errors.append("올바른 이메일 형식이 아닙니다.")
        valid = False
    
    if phone and not validate_phone_number(phone):
        errors.append("올바른 전화번호 형식이 아닙니다.")
        valid = False
    
    # Display errors
    if errors:
        for error in errors:
            st.error(error)
    
    # Calculate BMI
    if height > 0 and weight > 0:
        bmi = weight / ((height/100) ** 2)
        st.info(f"BMI: {bmi:.1f}")
    
    form_data = {
        'name': name.strip(),
        'age': age,
        'gender': gender,
        'height': height,
        'weight': weight,
        'email': email.strip(),
        'phone': phone.strip()
    }
    
    return valid, form_data


def render_assessment_test_form(test_name: str, test_config: Dict[str, Any], key_prefix: str = "") -> Dict[str, Any]:
    """Render individual assessment test form"""
    st.subheader(test_config['title'])
    
    if 'description' in test_config:
        st.info(test_config['description'])
    
    test_data = {}
    
    # Render fields based on test configuration
    for field in test_config.get('fields', []):
        field_key = f"{key_prefix}{test_name}_{field['name']}"
        
        if field['type'] == 'number':
            value = st.number_input(
                field['label'],
                min_value=field.get('min_value', 0),
                max_value=field.get('max_value', 1000),
                value=field.get('default_value', 0),
                step=field.get('step', 1),
                key=field_key
            )
            test_data[field['name']] = value
        
        elif field['type'] == 'selectbox':
            options = field.get('options', [])
            value = st.selectbox(
                field['label'],
                options=options,
                index=field.get('default_index', 0),
                key=field_key
            )
            test_data[field['name']] = value
        
        elif field['type'] == 'text_area':
            value = st.text_area(
                field['label'],
                max_chars=field.get('max_chars', 500),
                key=field_key
            )
            test_data[field['name']] = value
        
        elif field['type'] == 'checkbox':
            value = st.checkbox(
                field['label'],
                value=field.get('default_value', False),
                key=field_key
            )
            test_data[field['name']] = value
    
    return test_data


def render_search_form(placeholder: str = "검색어 입력", key: str = "search") -> str:
    """Render search form"""
    return st.text_input(
        "",
        placeholder=placeholder,
        key=key
    )


def render_date_range_form(key_prefix: str = "") -> Tuple[datetime, datetime]:
    """Render date range selection form"""
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=datetime.now().replace(day=1),
            key=f"{key_prefix}start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=datetime.now(),
            key=f"{key_prefix}end_date"
        )
    
    return datetime.combine(start_date, datetime.min.time()), datetime.combine(end_date, datetime.max.time())


def render_filter_form(filter_options: Dict[str, Any], key_prefix: str = "") -> Dict[str, Any]:
    """Render filter form"""
    filters = {}
    
    for filter_name, config in filter_options.items():
        filter_key = f"{key_prefix}filter_{filter_name}"
        
        if config['type'] == 'selectbox':
            value = st.selectbox(
                config['label'],
                options=config['options'],
                index=config.get('default_index', 0),
                key=filter_key
            )
            filters[filter_name] = value
        
        elif config['type'] == 'multiselect':
            value = st.multiselect(
                config['label'],
                options=config['options'],
                default=config.get('default', []),
                key=filter_key
            )
            filters[filter_name] = value
        
        elif config['type'] == 'slider':
            value = st.slider(
                config['label'],
                min_value=config['min_value'],
                max_value=config['max_value'],
                value=config.get('default', (config['min_value'], config['max_value'])),
                key=filter_key
            )
            filters[filter_name] = value
    
    return filters


def render_confirmation_dialog(message: str, key: str = "confirm") -> bool:
    """Render confirmation dialog"""
    st.warning(message)
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = st.button("확인", key=f"{key}_yes", type="primary")
    with col2:
        cancel = st.button("취소", key=f"{key}_no")
    
    return confirm