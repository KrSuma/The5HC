# This file makes the views directory a Python package

# Import views from the original views file
from ..views_original import (
    ClientViewSet, AssessmentViewSet, SessionPackageViewSet,
    SessionViewSet, PaymentViewSet, UserViewSet,
    CustomTokenObtainPairView
)

# Import MCQ views
from .mcq_views import (
    QuestionCategoryViewSet,
    MultipleChoiceQuestionViewSet,
    MCQAssessmentAPIView,
    MCQAnalyticsViewSet
)