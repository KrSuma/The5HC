# app.py - Main Streamlit application with improvements

import streamlit as st
import matplotlib

matplotlib.use('Agg')  # Required for non-interactive environments

# Import service layer instead of direct database access
from service_layer import (
    AppInitService, AuthService, ClientService,
    AssessmentService, DashboardService, AnalyticsService
)

# Import UI pages
# Note: In a real implementation, these would be updated to use the service layer
# For now, we'll reuse the original logic but note where improvements should be made
from ui_pages import (
    login_register_page, dashboard_page, dashboard_page_with_search,
    clients_page, client_detail_page, assessment_detail_page
)

# Import our enhanced assessment page
from improved_assessment_page import new_assessment_page

# Import simplified add client page for direct client addition
from simplified_add_client import simplified_add_client_page


def main():
    """Main application function with improvements"""

    # Initialize application
    AppInitService.initialize_app()

    # Check font availability
    fonts_available = AppInitService.check_fonts_availability()

    st.set_page_config(
        page_title = "더파이브 헬스케어 Fitness Assessment",
        page_icon = "🏋️",
        layout = "wide"
    )

    # Add custom CSS
    st.markdown("""
    <style>
    .download-button {
        display: inline-block;
        padding: 10px 20px;
        background-color: #ff4b4b;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
    .stProgress > div > div > div {
        background-color: #ff4b4b;
    }
    .error-message {
        color: #ff4b4b;
        padding: 10px;
        background-color: #ffeeee;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success-message {
        color: #4bb543;
        padding: 10px;
        background-color: #eeffee;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-message {
        color: #3498db;
        padding: 10px;
        background-color: #eef6ff;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html = True)

    # Session state initialization with error handling
    for key, default in [
        ('logged_in', False),
        ('trainer_id', None),
        ('trainer_name', None),
        ('current_page', "login"),
        ('selected_client', None),
        ('selected_assessment', None),
        ('use_simplified_assessment', False),
        ('use_search_dashboard', False),
        ('use_direct_client_add', True),  # Use the simplified client adding by default for now
        ('error_message', None),
        ('success_message', None),
        ('info_message', None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Page header
    st.title("더파이브 헬스케어 Fitness Assessment System")

    # Display font warning if needed
    if not all(fonts_available.values()):
        st.warning(
            "일부 한글 폰트가 설치되지 않았습니다. PDF 생성에 문제가 있을 수 있습니다. " +
            "필요한 폰트: " + ", ".join([k for k, v in fonts_available.items() if not v])
        )

    # Display any error messages
    if st.session_state.error_message:
        st.markdown(f'<div class="error-message">{st.session_state.error_message}</div>', unsafe_allow_html = True)
        st.session_state.error_message = None

    # Display any success messages
    if st.session_state.success_message:
        st.markdown(f'<div class="success-message">{st.session_state.success_message}</div>', unsafe_allow_html = True)
        st.session_state.success_message = None

    # Display any info messages
    if st.session_state.info_message:
        st.markdown(f'<div class="info-message">{st.session_state.info_message}</div>', unsafe_allow_html = True)
        st.session_state.info_message = None

    # Login / Registration Page
    if not st.session_state.logged_in:
        login_register_page()
    else:
        # Sidebar with navigation
        with st.sidebar:
            st.write(f"로그인: **{st.session_state.trainer_name}**")
            st.divider()

            if st.button("대시보드", use_container_width = True):
                st.session_state.current_page = "dashboard"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None

            if st.button("회원 관리", use_container_width = True):
                st.session_state.current_page = "clients"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None

            if st.button("새 회원 추가", use_container_width = True):
                st.session_state.current_page = "add_client"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None

            if st.button("새 평가", use_container_width = True):
                st.session_state.current_page = "new_assessment"
                st.session_state.selected_assessment = None

            st.divider()

            # Options
            st.subheader("옵션")
            st.checkbox("검색 기능이 있는 대시보드 사용",
                        key = "use_search_dashboard",
                        value = st.session_state.use_search_dashboard)

            st.checkbox("체크박스가 있는 간소화된 평가 폼 사용",
                        key = "use_simplified_assessment",
                        value = st.session_state.use_simplified_assessment)

            st.checkbox("직접 추가 방식으로 회원 추가",
                        key = "use_direct_client_add",
                        value = st.session_state.use_direct_client_add)

            st.divider()
            if st.button("로그아웃", use_container_width = True):
                st.session_state.logged_in = False
                st.session_state.trainer_id = None
                st.session_state.trainer_name = None
                st.session_state.current_page = "login"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None
                st.session_state.success_message = "로그아웃 되었습니다."
                st.rerun()

        # Main content area with error handling
        try:
            if st.session_state.current_page == "dashboard":
                if st.session_state.use_search_dashboard:
                    dashboard_page_with_search()
                else:
                    dashboard_page()
            elif st.session_state.current_page == "clients":
                clients_page()
            elif st.session_state.current_page == "add_client":
                simplified_add_client_page()
            elif st.session_state.current_page == "client_detail":
                client_detail_page()
            elif st.session_state.current_page == "new_assessment":
                # Always use our improved assessment page
                new_assessment_page()
            elif st.session_state.current_page == "assessment_detail":
                assessment_detail_page()
        except Exception as e:
            st.error(f"페이지 로딩 중 오류가 발생했습니다: {str(e)}")
            st.session_state.error_message = "페이지 로딩 중 오류가 발생했습니다. 다시 시도해주세요."
            st.session_state.current_page = "dashboard"
            st.rerun()


if __name__ == "__main__":
    main()