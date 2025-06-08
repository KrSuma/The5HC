"""
Enhanced Session Management Page with VAT and Fee Display
"""
import streamlit as st
from datetime import datetime, date, timedelta
from src.services.service_layer import SessionManagementService, ClientService
from src.utils.fee_calculator import FeeCalculator, CurrencyFormatter


def enhanced_session_management_page():
    """Enhanced session and credit management page with fee breakdown"""
    st.title("세션 및 크레딧 관리")
    
    if 'selected_client_id' not in st.session_state:
        st.warning("세션을 관리할 고객을 먼저 선택해주세요.")
        if st.button("고객 목록으로 돌아가기"):
            st.session_state.current_page = "clients"
            st.rerun()
        return
    
    client_id = st.session_state.selected_client_id
    
    try:
        # Get client details
        client = ClientService.get_client_details(client_id)
        if not client:
            st.error("고객 정보를 찾을 수 없습니다.")
            return
        
        st.header(f"{client['name']} - 세션 관리")
        
        # Initialize services
        session_service = SessionManagementService()
        fee_calculator = FeeCalculator()
        formatter = CurrencyFormatter()
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs(["패키지 관리", "세션 일정", "세션 기록", "결제 내역"])
        
        with tab1:
            st.subheader("세션 패키지")
            
            # Create new package with fee calculation
            with st.expander("새 패키지 생성"):
                col1, col2 = st.columns(2)
                
                with col1:
                    gross_amount = st.number_input(
                        "총 충전액 (VAT, 수수료 포함)", 
                        min_value=0, 
                        value=1980000, 
                        step=10000,
                        help="고객이 실제로 결제하는 금액"
                    )
                    
                    session_price = st.number_input(
                        "세션당 가격", 
                        min_value=1000, 
                        value=60000, 
                        step=5000,
                        help="개별 세션의 가격"
                    )
                
                with col2:
                    # Real-time fee calculation display
                    if gross_amount > 0:
                        breakdown = fee_calculator.calculate_fee_breakdown(gross_amount)
                        
                        st.info("**요금 계산 내역**")
                        st.caption(f"총 충전액: {formatter.format(breakdown['gross_amount'])}")
                        st.caption(f"부가세 (10%): {formatter.format(breakdown['vat_amount'])}")
                        st.caption(f"카드 수수료 (3.5%): {formatter.format(breakdown['card_fee_amount'])}")
                        st.success(f"**순 크래딧: {formatter.format(breakdown['net_amount'])}**")
                        
                        if session_price > 0:
                            total_sessions = gross_amount // session_price
                            st.info(f"**제공 가능 세션: {total_sessions}회**")
                
                package_name = st.text_input(
                    "패키지 이름 (선택사항)", 
                    placeholder="예: 5회 집중 트레이닝"
                )
                
                notes = st.text_area(
                    "메모 (선택사항)", 
                    placeholder="패키지에 대한 추가 메모"
                )
                
                if st.button("패키지 생성"):
                    if gross_amount > 0 and session_price > 0:
                        try:
                            package_id = session_service.create_package_with_fees(
                                client_id, gross_amount, session_price, package_name, notes
                            )
                            st.success(f"패키지가 생성되었습니다! (ID: {package_id})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"패키지 생성 중 오류: {e}")
                    else:
                        st.error("유효한 금액과 세션 가격을 입력해주세요.")
            
            # Display existing packages with fee breakdown
            st.subheader("기존 패키지")
            
            try:
                packages = session_service.get_client_packages(client_id, active_only=False)
                
                if packages:
                    for package in packages:
                        # Use fee data directly from package object if available
                        if hasattr(package, 'gross_amount') and package.gross_amount:
                            fee_data = {
                                'gross_amount': package.gross_amount,
                                'vat_amount': package.vat_amount or 0,
                                'card_fee_amount': package.card_fee_amount or 0,
                                'net_amount': package.net_amount or package.total_amount,
                                'vat_rate': package.vat_rate or 0.10,
                                'card_fee_rate': package.card_fee_rate or 0.035
                            }
                            # Calculate usage data
                            net_amount = fee_data['net_amount']
                            used_credits = net_amount - package.remaining_credits if net_amount else 0
                            usage_data = {
                                'used_credits': used_credits,
                                'remaining_credits': package.remaining_credits,
                                'utilization_percentage': (used_credits / net_amount * 100) if net_amount > 0 else 0
                            }
                        else:
                            # Fallback for packages without fee data
                            fee_data = {}
                            usage_data = {}
                        
                        with st.container():
                            # Package header
                            package_title = package.package_name or f"패키지 #{package.id}"
                            status_color = "green" if package.is_active else "red"
                            status_text = "활성" if package.is_active else "비활성"
                            
                            st.markdown(f"### {package_title} :{status_color}[{status_text}]")
                            
                            # Handle date formatting
                            if isinstance(package.created_at, str):
                                created_date = package.created_at[:10]
                            else:
                                created_date = package.created_at.strftime("%Y-%m-%d")
                            st.caption(f"생성일: {created_date}")
                            
                            # Fee breakdown section
                            if fee_data:
                                with st.expander("💰 요금 상세 내역", expanded=True):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("#### 충전 내역")
                                        st.metric("총 충전액", formatter.format(fee_data.get('gross_amount', package.total_amount)))
                                        st.caption(f"부가세 (10%): {formatter.format(fee_data.get('vat_amount', 0))}")
                                        st.caption(f"카드 수수료 (3.5%): {formatter.format(fee_data.get('card_fee_amount', 0))}")
                                        st.metric("순 잔여 크래딧", formatter.format(fee_data.get('net_amount', package.total_amount)))
                                    
                                    with col2:
                                        st.markdown("#### 사용 현황")
                                        used_credits = usage_data.get('used_credits', 0)
                                        remaining_credits = usage_data.get('remaining_credits', package.remaining_credits)
                                        
                                        st.metric("사용 크래딧", formatter.format(used_credits))
                                        st.metric("남은 크래딧", formatter.format(remaining_credits))
                                        
                                        # Progress bar
                                        utilization = usage_data.get('utilization_percentage', 0)
                                        st.progress(utilization / 100)
                                        st.caption(f"이용률: {utilization:.1f}%")
                            else:
                                # Fallback display for packages without fee data
                                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                                
                                with col1:
                                    st.metric("총 금액", formatter.format(package.total_amount))
                                
                                with col2:
                                    st.metric("잔여 크래딧", formatter.format(package.remaining_credits))
                                
                                with col3:
                                    st.metric("잔여 세션", f"{package.remaining_sessions}회")
                                
                                with col4:
                                    utilization = ((package.total_sessions - package.remaining_sessions) / package.total_sessions * 100) if package.total_sessions > 0 else 0
                                    st.metric("사용률", f"{utilization:.1f}%")
                            
                            # Session information
                            with st.expander("🏃 세션 정보"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("총 세션", f"{package.total_sessions}회")
                                with col2:
                                    used_sessions = package.total_sessions - package.remaining_sessions
                                    st.metric("사용 세션", f"{used_sessions}회")
                                with col3:
                                    st.metric("남은 세션", f"{package.remaining_sessions}회")
                            
                            # Package actions
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                if package.is_active and st.button(f"크래딧 추가", key=f"add_credit_{package.id}"):
                                    st.session_state.add_credit_package_id = package.id
                            
                            with action_col2:
                                if st.button(f"상세 보기", key=f"detail_{package.id}"):
                                    st.session_state.selected_package_id = package.id
                                    st.session_state.show_package_detail = True
                            
                            st.divider()
                else:
                    st.info("아직 생성된 패키지가 없습니다.")
                    
            except Exception as e:
                st.error(f"패키지 정보를 불러오는 중 오류: {e}")
            
            # Add credit modal with fee calculation
            if hasattr(st.session_state, 'add_credit_package_id'):
                with st.expander("크래딧 추가", expanded=True):
                    add_col1, add_col2 = st.columns(2)
                    
                    with add_col1:
                        gross_credit_amount = st.number_input(
                            "추가할 금액 (VAT, 수수료 포함)", 
                            min_value=0, 
                            value=660000, 
                            step=10000
                        )
                        
                        payment_method = st.selectbox(
                            "결제 방법", 
                            ["카드", "현금", "계좌이체", "기타"]
                        )
                        
                        description = st.text_area("메모 (선택사항)")
                    
                    with add_col2:
                        # Show fee calculation for credit addition
                        if gross_credit_amount > 0:
                            add_breakdown = fee_calculator.calculate_fee_breakdown(gross_credit_amount)
                            
                            st.info("**충전 계산 내역**")
                            st.caption(f"총 충전액: {formatter.format(add_breakdown['gross_amount'])}")
                            st.caption(f"부가세 (10%): {formatter.format(add_breakdown['vat_amount'])}")
                            st.caption(f"카드 수수료 (3.5%): {formatter.format(add_breakdown['card_fee_amount'])}")
                            st.success(f"**실제 충전 크래딧: {formatter.format(add_breakdown['net_amount'])}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("크래딧 추가"):
                            try:
                                session_service.add_credits_with_fees(
                                    client_id, gross_credit_amount, payment_method, description
                                )
                                st.success(f"{formatter.format(gross_credit_amount)} 충전 완료!")
                                del st.session_state.add_credit_package_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"크래딧 추가 중 오류: {e}")
                    
                    with col2:
                        if st.button("취소"):
                            del st.session_state.add_credit_package_id
                            st.rerun()
        
        with tab2:
            st.subheader("세션 일정 관리")
            
            # Get active packages for session scheduling
            try:
                active_packages = session_service.get_client_packages(client_id, active_only=True)
                
                if not active_packages:
                    st.warning("활성화된 패키지가 없습니다. 먼저 패키지를 생성해주세요.")
                else:
                    # Schedule new session
                    with st.expander("새 세션 예약"):
                        package_options = {
                            f"패키지 #{pkg.id} (잔여: {pkg.remaining_sessions}회)": pkg.id 
                            for pkg in active_packages if pkg.remaining_sessions > 0
                        }
                        
                        if not package_options:
                            st.warning("사용 가능한 세션이 있는 패키지가 없습니다.")
                        else:
                            selected_package = st.selectbox(
                                "패키지 선택", 
                                options=list(package_options.keys())
                            )
                            package_id = package_options[selected_package]
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                session_date = st.date_input(
                                    "세션 날짜", 
                                    value=date.today() + timedelta(days=1),
                                    min_value=date.today()
                                )
                                
                                session_time = st.time_input(
                                    "세션 시간", 
                                    value=None
                                )
                            
                            with col2:
                                session_duration = st.number_input(
                                    "세션 시간 (분)", 
                                    min_value=30, 
                                    max_value=180, 
                                    value=60, 
                                    step=15
                                )
                                
                                session_notes = st.text_area(
                                    "세션 메모", 
                                    placeholder="세션에 대한 메모나 특별 사항"
                                )
                            
                            if st.button("세션 예약"):
                                try:
                                    session_id = session_service.schedule_session(
                                        client_id, package_id, 
                                        session_date.strftime("%Y-%m-%d"),
                                        session_time.strftime("%H:%M") if session_time else None,
                                        session_duration, session_notes
                                    )
                                    st.success(f"세션이 예약되었습니다! (ID: {session_id})")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"세션 예약 중 오류: {e}")
                    
                    # Display scheduled sessions
                    st.subheader("예약된 세션")
                    
                    scheduled_sessions = session_service.get_client_sessions(client_id, status='scheduled')
                    
                    if scheduled_sessions:
                        for session in scheduled_sessions:
                            with st.container():
                                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                                
                                with col1:
                                    session_datetime = f"{session.session_date}"
                                    if session.session_time:
                                        session_datetime += f" {session.session_time}"
                                    st.write(f"**{session_datetime}**")
                                    if session.notes:
                                        st.caption(session.notes)
                                
                                with col2:
                                    st.write(f"{session.session_duration}분")
                                
                                with col3:
                                    st.write(formatter.format(session.session_cost))
                                
                                with col4:
                                    col_a, col_b = st.columns(2)
                                    
                                    with col_a:
                                        if st.button("완료", key=f"complete_{session.id}"):
                                            try:
                                                session_service.complete_session(session.id)
                                                st.success("세션이 완료되었습니다!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"세션 완료 중 오류: {e}")
                                    
                                    with col_b:
                                        if st.button("취소", key=f"cancel_{session.id}"):
                                            try:
                                                session_service.cancel_session(session.id, "사용자 취소")
                                                st.info("세션이 취소되었습니다.")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"세션 취소 중 오류: {e}")
                                
                                st.divider()
                    else:
                        st.info("예약된 세션이 없습니다.")
                        
            except Exception as e:
                st.error(f"세션 정보를 불러오는 중 오류: {e}")
        
        with tab3:
            st.subheader("세션 기록")
            
            try:
                completed_sessions = session_service.get_client_sessions(client_id, status='completed')
                
                if completed_sessions:
                    # Summary statistics
                    total_completed = len(completed_sessions)
                    total_cost = sum(s.session_cost for s in completed_sessions)
                    total_duration = sum(s.session_duration for s in completed_sessions)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("완료된 세션", f"{total_completed}회")
                    with col2:
                        st.metric("총 비용", formatter.format(total_cost))
                    with col3:
                        st.metric("총 시간", f"{total_duration}분")
                    
                    st.divider()
                    
                    # Session history
                    for session in completed_sessions:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                session_datetime = f"{session.session_date}"
                                if session.session_time:
                                    session_datetime += f" {session.session_time}"
                                st.write(f"**{session_datetime}** ({session.session_duration}분)")
                                if session.notes:
                                    st.caption(session.notes)
                            
                            with col2:
                                st.write(formatter.format(session.session_cost))
                            
                            with col3:
                                if isinstance(session.completed_at, str):
                                    completed_date = session.completed_at[:10]
                                else:
                                    completed_date = session.completed_at.strftime("%Y-%m-%d") if session.completed_at else "N/A"
                                st.caption(f"완료: {completed_date}")
                            
                            st.divider()
                else:
                    st.info("완료된 세션이 없습니다.")
                    
            except Exception as e:
                st.error(f"세션 기록을 불러오는 중 오류: {e}")
        
        with tab4:
            st.subheader("결제 내역")
            
            try:
                # Get enhanced payment history with fee breakdown
                payments = session_service.get_enhanced_payment_history(client_id)
                
                if payments:
                    # Summary
                    total_gross = sum(p.gross_amount or p.amount for p in payments)
                    total_vat = sum(p.vat_amount or 0 for p in payments)
                    total_fees = sum(p.card_fee_amount or 0 for p in payments)
                    total_net = sum(p.net_amount or p.amount for p in payments)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("총 결제액", formatter.format(total_gross))
                    with col2:
                        st.metric("총 부가세", formatter.format(total_vat))
                    with col3:
                        st.metric("총 수수료", formatter.format(total_fees))
                    with col4:
                        st.metric("순 금액", formatter.format(total_net))
                    
                    st.divider()
                    
                    # Payment history with fee breakdown
                    for payment in payments:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            
                            with col1:
                                st.write(f"**{payment.payment_date}**")
                                st.caption(payment.description or "결제")
                            
                            with col2:
                                if payment.gross_amount and payment.gross_amount != payment.amount:
                                    st.write(f"총액: {formatter.format(payment.gross_amount)}")
                                    st.caption(f"VAT: {formatter.format(payment.vat_amount or 0)} | "
                                             f"수수료: {formatter.format(payment.card_fee_amount or 0)}")
                                else:
                                    st.write(formatter.format(payment.amount))
                            
                            with col3:
                                if payment.net_amount:
                                    st.write(f"**순액: {formatter.format(payment.net_amount)}**")
                                
                            with col4:
                                st.caption(payment.payment_method or "카드")
                            
                            # Expandable details
                            if payment.gross_amount and st.button("상세", key=f"payment_detail_{payment.id}"):
                                with st.expander("결제 상세 내역", expanded=True):
                                    detail_col1, detail_col2 = st.columns(2)
                                    
                                    with detail_col1:
                                        st.metric("총 결제액", formatter.format(payment.gross_amount))
                                        st.metric("부가세 (10%)", formatter.format(payment.vat_amount or 0))
                                        st.metric("카드 수수료 (3.5%)", formatter.format(payment.card_fee_amount or 0))
                                    
                                    with detail_col2:
                                        st.metric("순 금액", formatter.format(payment.net_amount))
                                        if payment.vat_rate:
                                            st.caption(f"VAT율: {payment.vat_rate * 100:.1f}%")
                                        if payment.card_fee_rate:
                                            st.caption(f"수수료율: {payment.card_fee_rate * 100:.1f}%")
                            
                            st.divider()
                else:
                    st.info("결제 내역이 없습니다.")
                    
            except Exception as e:
                st.error(f"결제 내역을 불러오는 중 오류: {e}")
                
    except Exception as e:
        st.error(f"페이지 로딩 중 오류가 발생했습니다: {e}")
        import traceback
        st.error(traceback.format_exc())