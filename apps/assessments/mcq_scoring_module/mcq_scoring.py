"""
MCQ Scoring Engine for The5HC Fitness Assessment System.

This module handles scoring for Multiple Choice Questions across three categories:
- Knowledge (15% of comprehensive score)
- Lifestyle (15% of comprehensive score)
- Readiness (10% of comprehensive score)

Physical assessments contribute the remaining 60% of the comprehensive score.
"""

from typing import Dict, List, Tuple, Optional
from django.db.models import Sum, Q, F
from decimal import Decimal


class MCQScoringEngine:
    """
    Engine for calculating MCQ scores and integrating them with physical assessment scores.
    """
    
    # Category weights for comprehensive scoring
    CATEGORY_WEIGHTS = {
        'knowledge': 0.15,
        'lifestyle': 0.15,
        'readiness': 0.10,
        'physical': 0.60
    }
    
    def __init__(self, assessment):
        """
        Initialize the scoring engine with an assessment instance.
        
        Args:
            assessment: Assessment model instance
        """
        self.assessment = assessment
        self._category_scores = {}
        self._risk_factors = []
    
    def calculate_mcq_scores(self) -> Dict[str, float]:
        """
        Calculate scores for all MCQ categories.
        
        Returns:
            Dict with category scores and comprehensive score
        """
        # Get all question responses for this assessment
        responses = self.assessment.question_responses.select_related(
            'question__category'
        ).prefetch_related('selected_choices')
        
        # Group responses by category
        category_responses = {}
        for response in responses:
            category_name = response.question.category.name.lower()
            if category_name not in category_responses:
                category_responses[category_name] = []
            category_responses[category_name].append(response)
        
        # Calculate score for each category
        scores = {}
        for category_name, cat_responses in category_responses.items():
            scores[category_name] = self._calculate_category_score(
                category_name, cat_responses
            )
        
        # Store individual category scores
        self.assessment.knowledge_score = scores.get('knowledge', 0)
        self.assessment.lifestyle_score = scores.get('lifestyle', 0)
        self.assessment.readiness_score = scores.get('readiness', 0)
        
        # Calculate comprehensive score
        comprehensive_score = self._calculate_comprehensive_score(scores)
        self.assessment.comprehensive_score = comprehensive_score
        
        return {
            'knowledge_score': self.assessment.knowledge_score,
            'lifestyle_score': self.assessment.lifestyle_score,
            'readiness_score': self.assessment.readiness_score,
            'comprehensive_score': comprehensive_score,
            'mcq_risk_factors': self._risk_factors
        }
    
    def _calculate_category_score(self, category_name: str, 
                                  responses: List) -> float:
        """
        Calculate score for a single category.
        
        Args:
            category_name: Name of the category
            responses: List of QuestionResponse instances for this category
            
        Returns:
            Score as percentage (0-100)
        """
        if not responses:
            return 0.0
        
        total_possible_points = 0
        total_earned_points = 0
        
        for response in responses:
            # Get maximum possible points for this question
            max_points = response.question.points
            total_possible_points += max_points
            
            # Get earned points (already calculated in QuestionResponse.save())
            earned_points = response.points_earned
            total_earned_points += earned_points
            
            # Check for risk factors
            self._extract_risk_factors(response)
        
        # Calculate percentage score
        if total_possible_points > 0:
            score = (total_earned_points / total_possible_points) * 100
        else:
            score = 0.0
        
        # Store for later use
        self._category_scores[category_name] = score
        
        return round(score, 1)
    
    def _extract_risk_factors(self, response) -> None:
        """
        Extract risk factors from question responses.
        
        Args:
            response: QuestionResponse instance
        """
        for choice in response.selected_choices.all():
            if choice.contributes_to_risk and choice.risk_weight > 0:
                risk_factor = {
                    'category': response.question.category.name,
                    'question': response.question.question_text,
                    'answer': choice.choice_text,
                    'risk_weight': float(choice.risk_weight),
                    'risk_type': 'mcq_response'
                }
                self._risk_factors.append(risk_factor)
    
    def _calculate_comprehensive_score(self, mcq_scores: Dict[str, float]) -> float:
        """
        Calculate comprehensive score combining physical and MCQ assessments.
        
        Args:
            mcq_scores: Dictionary of MCQ category scores
            
        Returns:
            Comprehensive score (0-100)
        """
        # Get physical assessment score (use overall_score)
        physical_score = self.assessment.overall_score or 0
        
        # Calculate weighted MCQ contribution
        mcq_contribution = 0
        for category, weight in self.CATEGORY_WEIGHTS.items():
            if category == 'physical':
                continue
            score = mcq_scores.get(category, 0)
            mcq_contribution += score * weight
        
        # Calculate weighted physical contribution
        physical_contribution = physical_score * self.CATEGORY_WEIGHTS['physical']
        
        # Total comprehensive score
        comprehensive_score = physical_contribution + mcq_contribution
        
        return round(comprehensive_score, 1)
    
    def get_mcq_risk_factors(self) -> List[Dict]:
        """
        Get all MCQ-related risk factors.
        
        Returns:
            List of risk factor dictionaries
        """
        return self._risk_factors
    
    def calculate_mcq_risk_contribution(self) -> float:
        """
        Calculate how much MCQ responses contribute to overall injury risk.
        
        Returns:
            Risk contribution score (0-100)
        """
        if not self._risk_factors:
            return 0.0
        
        # Sum up risk weights (max 1.0 per factor)
        total_risk_weight = sum(
            min(factor['risk_weight'], 1.0) 
            for factor in self._risk_factors
        )
        
        # Normalize to 0-100 scale
        # Assume max 10 risk factors for normalization
        max_expected_risk = 10.0
        risk_score = min((total_risk_weight / max_expected_risk) * 100, 100)
        
        return round(risk_score, 1)
    
    def get_category_insights(self) -> Dict[str, Dict]:
        """
        Get detailed insights for each MCQ category.
        
        Returns:
            Dictionary with insights per category
        """
        insights = {}
        
        # Knowledge insights
        knowledge_score = self._category_scores.get('knowledge', 0)
        insights['knowledge'] = {
            'score': knowledge_score,
            'interpretation': self._interpret_score(knowledge_score),
            'recommendations': self._get_knowledge_recommendations(knowledge_score)
        }
        
        # Lifestyle insights
        lifestyle_score = self._category_scores.get('lifestyle', 0)
        insights['lifestyle'] = {
            'score': lifestyle_score,
            'interpretation': self._interpret_score(lifestyle_score),
            'recommendations': self._get_lifestyle_recommendations(lifestyle_score)
        }
        
        # Readiness insights
        readiness_score = self._category_scores.get('readiness', 0)
        insights['readiness'] = {
            'score': readiness_score,
            'interpretation': self._interpret_score(readiness_score),
            'recommendations': self._get_readiness_recommendations(readiness_score)
        }
        
        return insights
    
    def _interpret_score(self, score: float) -> str:
        """
        Interpret a score with Korean description.
        
        Args:
            score: Score value (0-100)
            
        Returns:
            Korean interpretation string
        """
        if score >= 90:
            return "매우 우수"
        elif score >= 80:
            return "우수"
        elif score >= 70:
            return "양호"
        elif score >= 60:
            return "보통"
        else:
            return "개선 필요"
    
    def _get_knowledge_recommendations(self, score: float) -> List[str]:
        """
        Get recommendations based on knowledge score.
        
        Args:
            score: Knowledge score (0-100)
            
        Returns:
            List of Korean recommendations
        """
        recommendations = []
        
        if score < 60:
            recommendations.extend([
                "운동 원리와 기술에 대한 교육이 필요합니다",
                "트레이너와 함께 올바른 운동 자세를 학습하세요",
                "기본적인 영양 지식을 습득하는 것이 중요합니다"
            ])
        elif score < 80:
            recommendations.extend([
                "운동 프로그램의 원리를 더 깊이 이해하면 좋겠습니다",
                "영양과 회복에 대한 지식을 보완하세요"
            ])
        else:
            recommendations.append("훌륭한 운동 지식을 가지고 있습니다. 지속적으로 최신 정보를 습득하세요")
        
        return recommendations
    
    def _get_lifestyle_recommendations(self, score: float) -> List[str]:
        """
        Get recommendations based on lifestyle score.
        
        Args:
            score: Lifestyle score (0-100)
            
        Returns:
            List of Korean recommendations
        """
        recommendations = []
        
        if score < 60:
            recommendations.extend([
                "수면 패턴을 개선하여 7-8시간의 충분한 수면을 취하세요",
                "스트레스 관리 방법을 찾아 실천하세요",
                "규칙적인 식사 시간과 균형잡힌 영양 섭취가 필요합니다"
            ])
        elif score < 80:
            recommendations.extend([
                "생활 습관의 일관성을 높이면 운동 효과가 향상됩니다",
                "충분한 수분 섭취를 유지하세요"
            ])
        else:
            recommendations.append("건강한 생활 습관을 잘 유지하고 있습니다. 계속 유지하세요")
        
        return recommendations
    
    def _get_readiness_recommendations(self, score: float) -> List[str]:
        """
        Get recommendations based on readiness score.
        
        Args:
            score: Readiness score (0-100)
            
        Returns:
            List of Korean recommendations
        """
        recommendations = []
        
        if score < 60:
            recommendations.extend([
                "현재 신체 상태를 고려하여 운동 강도를 조절하세요",
                "충분한 회복 시간을 가진 후 운동하세요",
                "통증이나 불편함이 있다면 전문가 상담을 받으세요"
            ])
        elif score < 80:
            recommendations.extend([
                "운동 전 충분한 준비운동을 하세요",
                "목표를 명확히 하여 동기부여를 높이세요"
            ])
        else:
            recommendations.append("운동할 준비가 잘 되어 있습니다. 안전하게 운동하세요")
        
        return recommendations


def calculate_mcq_scores_for_assessment(assessment) -> Dict[str, float]:
    """
    Convenience function to calculate MCQ scores for an assessment.
    
    Args:
        assessment: Assessment model instance
        
    Returns:
        Dictionary with all MCQ scores
    """
    engine = MCQScoringEngine(assessment)
    return engine.calculate_mcq_scores()


def integrate_mcq_risk_factors(existing_risk_factors: Dict, 
                              mcq_risk_factors: List[Dict]) -> Dict:
    """
    Integrate MCQ risk factors with existing physical assessment risk factors.
    
    Args:
        existing_risk_factors: Current risk factors from physical assessment
        mcq_risk_factors: Risk factors from MCQ responses
        
    Returns:
        Updated risk factors dictionary
    """
    if not existing_risk_factors:
        existing_risk_factors = {}
    
    # Add MCQ risk factors to the lifestyle category
    if 'lifestyle_factors' not in existing_risk_factors:
        existing_risk_factors['lifestyle_factors'] = []
    
    existing_risk_factors['lifestyle_factors'].extend(mcq_risk_factors)
    
    # Update risk summary
    if mcq_risk_factors:
        if 'risk_summary' not in existing_risk_factors:
            existing_risk_factors['risk_summary'] = []
        
        existing_risk_factors['risk_summary'].append({
            'category': 'MCQ Assessment',
            'risk_count': len(mcq_risk_factors),
            'severity': 'moderate' if len(mcq_risk_factors) > 3 else 'low'
        })
    
    return existing_risk_factors