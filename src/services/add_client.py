"""
Simplified client addition page
"""
import streamlit as st
from src.services.service_layer import ClientService


def simplified_add_client_page():
    """Simplified page for adding new clients"""
    st.title("새 회원 추가")
    
    with st.form("add_client_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("이름*", placeholder="회원 이름을 입력하세요")
            age = st.number_input("나이*", min_value=1, max_value=120, value=30)
            gender = st.selectbox("성별*", ["남성", "여성"])
        
        with col2:
            height = st.number_input("키 (cm)*", min_value=50.0, max_value=250.0, value=170.0, step=0.1)
            weight = st.number_input("체중 (kg)*", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
        
        email = st.text_input("이메일", placeholder="example@email.com")
        phone = st.text_input("연락처", placeholder="010-1234-5678")
        
        submitted = st.form_submit_button("회원 추가", use_container_width=True)
        
        if submitted:
            if not name or not age or not gender or not height or not weight:
                st.error("필수 항목(*)을 모두 입력해주세요.")
            else:
                try:
                    # Get trainer_id from session state
                    trainer_id = st.session_state.get('trainer_id')
                    if not trainer_id:
                        st.error("로그인이 필요합니다.")
                        return
                    
                    success, message = ClientService.add_client(
                        trainer_id=trainer_id,
                        name=name,
                        age=age,
                        gender=gender,
                        height=height,
                        weight=weight,
                        email=email if email else "",
                        phone=phone if phone else ""
                    )
                    
                    if success:
                        st.success(f"회원이 성공적으로 추가되었습니다: {name}")
                        st.session_state.current_page = "clients"
                        st.rerun()
                    else:
                        st.error(f"회원 추가 실패: {message}")
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
    
    # Back button
    if st.button("회원 목록으로 돌아가기"):
        st.session_state.current_page = "clients"
        st.rerun()