"""
Dashboard page
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from ...services.client_service import ClientService
from ...services.assessment_service import AssessmentService
from ..components.charts import render_stats_chart, render_progress_chart


def render_dashboard():
    """Render main dashboard"""
    st.title("대시보드")
    
    trainer_id = st.session_state.get('trainer_id')
    username = st.session_state.get('username', 'Unknown')
    
    st.write(f"안녕하세요, {username}님! 👋")
    
    # Get services
    client_service = ClientService()
    assessment_service = AssessmentService()
    
    # Get statistics
    client_stats = client_service.get_client_stats(trainer_id)
    trainer_stats = assessment_service.get_trainer_stats(trainer_id)
    
    # Display summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="총 고객 수",
            value=client_stats['total_clients']
        )
    
    with col2:
        st.metric(
            label="총 평가 수",
            value=trainer_stats['total_assessments']
        )
    
    with col3:
        st.metric(
            label="평균 점수",
            value=f"{trainer_stats['avg_overall_score']}/100"
        )
    
    with col4:
        st.metric(
            label="개선율",
            value=f"{trainer_stats['improvement_rate']}%"
        )
    
    st.divider()
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("최근 등록된 고객")
        clients = client_service.get_clients(trainer_id)
        if clients:
            recent_clients = sorted(clients, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
            for client in recent_clients:
                with st.container():
                    st.write(f"**{client.name}** ({client.age}세, {client.gender})")
                    st.caption(f"BMI: {client.bmi} | 등록일: {client.created_at.strftime('%Y-%m-%d') if client.created_at else 'N/A'}")
        else:
            st.info("등록된 고객이 없습니다.")
    
    with col2:
        st.subheader("최근 평가")
        if clients:
            recent_assessments = []
            for client in clients:
                latest = assessment_service.get_latest_assessment(client.id)
                if latest:
                    recent_assessments.append((client, latest))
            
            # Sort by assessment date
            recent_assessments.sort(key=lambda x: x[1].date, reverse=True)
            
            for client, assessment in recent_assessments[:5]:
                with st.container():
                    st.write(f"**{client.name}** - 종합 점수: {assessment.overall_score:.1f}/100")
                    st.caption(f"평가일: {assessment.date}")
        else:
            st.info("진행된 평가가 없습니다.")
    
    st.divider()
    
    # Charts section
    if client_stats['total_clients'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("고객 성별 분포")
            gender_data = client_stats['gender_distribution']
            if sum(gender_data.values()) > 0:
                render_stats_chart(gender_data, chart_type='pie')
        
        with col2:
            st.subheader("점수 분포")
            if trainer_stats['total_assessments'] > 0:
                # Get all latest assessments for score distribution
                score_data = []
                for client in clients:
                    latest = assessment_service.get_latest_assessment(client.id)
                    if latest and latest.overall_score:
                        score_data.append(latest.overall_score)
                
                if score_data:
                    # Create score ranges
                    ranges = {'Excellent (85+)': 0, 'Good (70-84)': 0, 'Average (50-69)': 0, 'Needs Attention (<50)': 0}
                    for score in score_data:
                        if score >= 85:
                            ranges['Excellent (85+)'] += 1
                        elif score >= 70:
                            ranges['Good (70-84)'] += 1
                        elif score >= 50:
                            ranges['Average (50-69)'] += 1
                        else:
                            ranges['Needs Attention (<50)'] += 1
                    
                    render_stats_chart(ranges, chart_type='bar')
    
    # Quick actions
    st.divider()
    st.subheader("빠른 작업")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("새 고객 등록", use_container_width=True):
            st.session_state.current_page = "clients"
            st.session_state.show_add_client = True
            st.rerun()
    
    with col2:
        if st.button("평가 진행", use_container_width=True):
            st.session_state.current_page = "assessment"
            st.rerun()
    
    with col3:
        if st.button("분석 보기", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()