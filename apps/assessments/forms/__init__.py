"""
Assessment forms module.
"""

from .assessment_forms import AssessmentForm, AssessmentSearchForm
from .mcq_forms import MCQResponseForm, CategoryMCQFormSet

# Export refactored forms as well
try:
    from .refactored_forms import (
        AssessmentBasicForm,
        OverheadSquatTestForm,
        PushUpTestForm,
        SingleLegBalanceTestForm,
        ToeTouchTestForm,
        ShoulderMobilityTestForm,
        FarmersCarryTestForm,
        HarvardStepTestForm,
        AssessmentWithTestsForm
    )
except ImportError:
    # Refactored forms not available yet
    pass