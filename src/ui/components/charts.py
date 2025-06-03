"""
Chart rendering components
"""
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


def render_stats_chart(data: Dict[str, Any], chart_type: str = 'bar', title: str = ""):
    """Render statistics chart"""
    if not data or not any(data.values()):
        st.info("No data to display.")
        return
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if chart_type == 'pie':
        # Filter out zero values for pie chart
        filtered_data = {k: v for k, v in data.items() if v > 0}
        if filtered_data:
            ax.pie(filtered_data.values(), labels=filtered_data.keys(), autopct='%1.1f%%')
            ax.set_title(title)
    
    elif chart_type == 'bar':
        bars = ax.bar(data.keys(), data.values())
        ax.set_title(title)
        ax.set_ylabel('Count')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_progress_chart(progress_data: List[Dict[str, Any]], title: str = "Progress"):
    """Render progress line chart"""
    if not progress_data:
        st.info("No progress data to display.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(progress_data)
    
    if 'date' not in df.columns:
        st.error("No date data available.")
        return
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot different score categories
    score_columns = ['overall_score', 'strength_score', 'mobility_score', 'balance_score', 'cardio_score']
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    labels = ['Overall', 'Strength', 'Mobility', 'Balance', 'Cardio']
    
    for i, (col, color, label) in enumerate(zip(score_columns, colors, labels)):
        if col in df.columns and df[col].notna().any():
            ax.plot(df['date'], df[col], marker='o', color=color, label=label, linewidth=2)
    
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Score')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)
    plt.close()


def render_comparison_chart(comparison_data: Dict[str, float], title: str = "Score Comparison"):
    """Render comparison chart showing improvements/declines"""
    if not comparison_data:
        st.info("No data to compare.")
        return
    
    # Separate positive and negative changes
    categories = []
    changes = []
    colors = []
    
    for category, change in comparison_data.items():
        if category.endswith('_change') and change != 0:
            cat_name = category.replace('_change', '').replace('_', ' ').title()
            categories.append(cat_name)
            changes.append(change)
            colors.append('green' if change > 0 else 'red')
    
    if not categories:
        st.info("No changes detected.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.barh(categories, changes, color=colors)
    ax.set_title(title)
    ax.set_xlabel('Score Change')
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for bar, change in zip(bars, changes):
        width = bar.get_width()
        ax.text(width + (0.5 if width > 0 else -0.5), bar.get_y() + bar.get_height()/2,
               f'{change:+.1f}', ha='left' if width > 0 else 'right', va='center')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_score_radar_chart(scores: Dict[str, float], title: str = "Overall Score"):
    """Render radar chart for assessment scores"""
    if not scores or not any(v for v in scores.values() if v is not None):
        st.info("No scores to display.")
        return
    
    # Prepare data
    categories = []
    values = []
    
    score_mapping = {
        'strength_score': 'Strength',
        'mobility_score': 'Mobility', 
        'balance_score': 'Balance',
        'cardio_score': 'Cardio'
    }
    
    for key, label in score_mapping.items():
        if key in scores and scores[key] is not None:
            categories.append(label)
            values.append(scores[key])
    
    if not categories:
        st.info("No scores to display.")
        return
    
    # Number of variables
    N = len(categories)
    
    # Compute angles for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    # Add first value to end to close the radar chart
    values += values[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # Plot
    ax.plot(angles, values, 'o-', linewidth=2, label=title)
    ax.fill(angles, values, alpha=0.25)
    
    # Add category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    # Set y-axis limits
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'])
    ax.grid(True)
    
    plt.title(title, size=16, y=1.08)
    plt.tight_layout()
    
    st.pyplot(fig)
    plt.close()


def render_assessment_history_chart(assessments: List[Dict[str, Any]], title: str = "Assessment History"):
    """Render assessment history chart"""
    if not assessments:
        st.info("No assessment history available.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(assessments)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Overall score trend
    if 'overall_score' in df.columns and df['overall_score'].notna().any():
        ax1.plot(df['date'], df['overall_score'], marker='o', linewidth=2, color='blue')
        ax1.set_title('Overall Score Trend')
        ax1.set_ylabel('Score')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
    
    # Category scores
    categories = ['strength_score', 'mobility_score', 'balance_score', 'cardio_score']
    labels = ['Strength', 'Mobility', 'Balance', 'Cardio']
    colors = ['red', 'green', 'orange', 'purple']
    
    for cat, label, color in zip(categories, labels, colors):
        if cat in df.columns and df[cat].notna().any():
            ax2.plot(df['date'], df[cat], marker='o', label=label, color=color, linewidth=2)
    
    ax2.set_title('Category Score Trends')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Score')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)
    
    # Format x-axis
    for ax in [ax1, ax2]:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()