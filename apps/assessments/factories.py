"""
Factory classes for the assessments app models.
Following django-test.md guidelines for pytest testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils import timezone
import random
from decimal import Decimal

from apps.assessments.models import Assessment
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory

fake = Faker('ko_KR')


class AssessmentFactory(DjangoModelFactory):
    """Factory for creating Assessment instances"""
    
    class Meta:
        model = Assessment
    
    # Relationships
    client = factory.SubFactory(ClientFactory)
    trainer = factory.LazyAttribute(lambda obj: obj.client.trainer if hasattr(obj, 'client') and obj.client else TrainerFactory())
    
    # Assessment metadata
    date = factory.LazyFunction(lambda: fake.date_time_this_month(tzinfo=timezone.get_current_timezone()))
    
    # Overhead Squat Test (0-5 scale)
    overhead_squat_score = factory.LazyFunction(lambda: random.randint(1, 5))
    overhead_squat_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Push-up Test
    push_up_reps = factory.LazyFunction(lambda: random.randint(5, 50))
    push_up_score = factory.LazyFunction(lambda: random.randint(1, 5))
    push_up_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Single Leg Balance Test (seconds)
    single_leg_balance_right_eyes_open = factory.LazyFunction(lambda: random.randint(10, 60))
    single_leg_balance_left_eyes_open = factory.LazyFunction(lambda: random.randint(10, 60))
    single_leg_balance_right_eyes_closed = factory.LazyFunction(lambda: random.randint(3, 30))
    single_leg_balance_left_eyes_closed = factory.LazyFunction(lambda: random.randint(3, 30))
    single_leg_balance_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Toe Touch Test
    toe_touch_distance = factory.LazyFunction(lambda: round(random.uniform(-15.0, 10.0), 1))
    toe_touch_score = factory.LazyFunction(lambda: random.randint(1, 5))
    toe_touch_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Shoulder Mobility Test
    shoulder_mobility_right = factory.LazyFunction(lambda: round(random.uniform(0.0, 15.0), 1))
    shoulder_mobility_left = factory.LazyFunction(lambda: round(random.uniform(0.0, 15.0), 1))
    shoulder_mobility_score = factory.LazyFunction(lambda: random.randint(1, 5))
    shoulder_mobility_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Farmer's Carry Test
    farmer_carry_weight = factory.LazyFunction(lambda: round(random.uniform(10.0, 50.0), 1))
    farmer_carry_distance = factory.LazyFunction(lambda: round(random.uniform(20.0, 100.0), 1))
    farmer_carry_time = factory.LazyFunction(lambda: random.randint(20, 60))
    farmer_carry_score = factory.LazyFunction(lambda: random.randint(1, 5))
    farmer_carry_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Harvard Step Test
    # Harvard Step Test - now split into 3 heart rate measurements
    harvard_step_test_hr1 = factory.LazyFunction(lambda: random.randint(120, 180))
    harvard_step_test_hr2 = factory.LazyFunction(lambda: random.randint(115, 175))
    harvard_step_test_hr3 = factory.LazyFunction(lambda: random.randint(110, 170))
    harvard_step_test_duration = factory.LazyFunction(lambda: round(random.uniform(60.0, 300.0), 1))
    harvard_step_test_notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Calculated scores (will be computed by model methods)
    overall_score = factory.LazyFunction(lambda: round(random.uniform(2.0, 4.5), 1))
    strength_score = factory.LazyFunction(lambda: round(random.uniform(2.0, 4.5), 1))
    mobility_score = factory.LazyFunction(lambda: round(random.uniform(2.0, 4.5), 1))
    balance_score = factory.LazyFunction(lambda: round(random.uniform(2.0, 4.5), 1))
    cardio_score = factory.LazyFunction(lambda: round(random.uniform(2.0, 4.5), 1))


class BasicAssessmentFactory(AssessmentFactory):
    """Factory for creating basic assessments with minimal data"""
    
    # Only include essential fields
    overhead_squat_score = factory.LazyFunction(lambda: random.randint(2, 4))
    push_up_reps = factory.LazyFunction(lambda: random.randint(10, 30))
    push_up_score = factory.LazyFunction(lambda: random.randint(2, 4))
    
    # Clear optional fields
    overhead_squat_notes = None
    push_up_notes = None
    single_leg_balance_notes = None
    toe_touch_notes = None
    shoulder_mobility_notes = None
    farmer_carry_notes = None
    harvard_step_test_notes = None


class ComprehensiveAssessmentFactory(AssessmentFactory):
    """Factory for creating comprehensive assessments with all fields filled"""
    
    # Ensure all notes are filled
    overhead_squat_notes = factory.LazyFunction(lambda: fake.paragraph())
    push_up_notes = factory.LazyFunction(lambda: fake.paragraph())
    single_leg_balance_notes = factory.LazyFunction(lambda: fake.paragraph())
    toe_touch_notes = factory.LazyFunction(lambda: fake.paragraph())
    shoulder_mobility_notes = factory.LazyFunction(lambda: fake.paragraph())
    farmer_carry_notes = factory.LazyFunction(lambda: fake.paragraph())
    harvard_step_test_notes = factory.LazyFunction(lambda: fake.paragraph())


class HighScoreAssessmentFactory(AssessmentFactory):
    """Factory for creating high-performing assessments"""
    
    overhead_squat_score = factory.LazyFunction(lambda: random.randint(4, 5))
    push_up_reps = factory.LazyFunction(lambda: random.randint(30, 50))
    push_up_score = factory.LazyFunction(lambda: random.randint(4, 5))
    single_leg_balance_right_eyes_open = factory.LazyFunction(lambda: random.randint(45, 60))
    single_leg_balance_left_eyes_open = factory.LazyFunction(lambda: random.randint(45, 60))
    single_leg_balance_right_eyes_closed = factory.LazyFunction(lambda: random.randint(20, 30))
    single_leg_balance_left_eyes_closed = factory.LazyFunction(lambda: random.randint(20, 30))
    toe_touch_distance = factory.LazyFunction(lambda: round(random.uniform(5.0, 10.0), 1))
    toe_touch_score = factory.LazyFunction(lambda: random.randint(4, 5))
    shoulder_mobility_right = factory.LazyFunction(lambda: round(random.uniform(0.0, 3.0), 1))
    shoulder_mobility_left = factory.LazyFunction(lambda: round(random.uniform(0.0, 3.0), 1))
    shoulder_mobility_score = factory.LazyFunction(lambda: random.randint(4, 5))
    farmer_carry_weight = factory.LazyFunction(lambda: round(random.uniform(30.0, 50.0), 1))
    farmer_carry_distance = factory.LazyFunction(lambda: round(random.uniform(80.0, 100.0), 1))
    farmer_carry_time = factory.LazyFunction(lambda: random.randint(20, 35))
    farmer_carry_score = factory.LazyFunction(lambda: random.randint(4, 5))
    # Harvard Step Test - good fitness
    harvard_step_test_hr1 = factory.LazyFunction(lambda: random.randint(120, 140))
    harvard_step_test_hr2 = factory.LazyFunction(lambda: random.randint(115, 135))
    harvard_step_test_hr3 = factory.LazyFunction(lambda: random.randint(110, 130))
    overall_score = factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))
    strength_score = factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))
    mobility_score = factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))
    balance_score = factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))
    cardio_score = factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))


class LowScoreAssessmentFactory(AssessmentFactory):
    """Factory for creating low-performing assessments"""
    
    overhead_squat_score = factory.LazyFunction(lambda: random.randint(1, 2))
    push_up_reps = factory.LazyFunction(lambda: random.randint(1, 10))
    push_up_score = factory.LazyFunction(lambda: random.randint(1, 2))
    single_leg_balance_right_eyes_open = factory.LazyFunction(lambda: random.randint(5, 15))
    single_leg_balance_left_eyes_open = factory.LazyFunction(lambda: random.randint(5, 15))
    single_leg_balance_right_eyes_closed = factory.LazyFunction(lambda: random.randint(1, 5))
    single_leg_balance_left_eyes_closed = factory.LazyFunction(lambda: random.randint(1, 5))
    toe_touch_distance = factory.LazyFunction(lambda: round(random.uniform(-15.0, -5.0), 1))
    toe_touch_score = factory.LazyFunction(lambda: random.randint(1, 2))
    shoulder_mobility_right = factory.LazyFunction(lambda: round(random.uniform(10.0, 15.0), 1))
    shoulder_mobility_left = factory.LazyFunction(lambda: round(random.uniform(10.0, 15.0), 1))
    shoulder_mobility_score = factory.LazyFunction(lambda: random.randint(1, 2))
    farmer_carry_weight = factory.LazyFunction(lambda: round(random.uniform(5.0, 15.0), 1))
    farmer_carry_distance = factory.LazyFunction(lambda: round(random.uniform(10.0, 30.0), 1))
    farmer_carry_time = factory.LazyFunction(lambda: random.randint(45, 80))
    farmer_carry_score = factory.LazyFunction(lambda: random.randint(1, 2))
    # Harvard Step Test - poor fitness
    harvard_step_test_hr1 = factory.LazyFunction(lambda: random.randint(160, 200))
    harvard_step_test_hr2 = factory.LazyFunction(lambda: random.randint(155, 195))
    harvard_step_test_hr3 = factory.LazyFunction(lambda: random.randint(150, 190))
    overall_score = factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))
    strength_score = factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))
    mobility_score = factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))
    balance_score = factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))
    cardio_score = factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))


class IncompleteAssessmentFactory(AssessmentFactory):
    """Factory for creating incomplete assessments (testing edge cases)"""
    
    # Only fill some fields, leave others as None/blank
    overhead_squat_score = factory.LazyFunction(lambda: random.randint(1, 5))
    push_up_reps = None
    push_up_score = None
    single_leg_balance_right_eyes_open = factory.LazyFunction(lambda: random.randint(10, 30))
    single_leg_balance_left_eyes_open = None
    single_leg_balance_right_eyes_closed = None
    single_leg_balance_left_eyes_closed = None
    toe_touch_distance = None
    toe_touch_score = None
    shoulder_mobility_right = None
    shoulder_mobility_left = None
    shoulder_mobility_score = None
    farmer_carry_weight = None
    farmer_carry_distance = None
    farmer_carry_time = None
    farmer_carry_score = None
    harvard_step_test_hr1 = None
    harvard_step_test_hr2 = None
    harvard_step_test_hr3 = None
    harvard_step_test_duration = None
    
    # Clear calculated scores
    overall_score = None
    strength_score = None
    mobility_score = None
    balance_score = None
    cardio_score = None


# Trait-based approach
class AssessmentWithTraitsFactory(AssessmentFactory):
    """
    Factory with traits for different assessment types.
    Usage:
    - AssessmentWithTraitsFactory()  # Regular assessment
    - AssessmentWithTraitsFactory(high_performer=True)  # High scores
    - AssessmentWithTraitsFactory(beginner=True)  # Low scores
    - AssessmentWithTraitsFactory(incomplete=True)  # Missing data
    """
    
    class Params:
        high_performer = factory.Trait(
            overhead_squat_score=factory.LazyFunction(lambda: random.randint(4, 5)),
            push_up_reps=factory.LazyFunction(lambda: random.randint(30, 50)),
            push_up_score=factory.LazyFunction(lambda: random.randint(4, 5)),
            overall_score=factory.LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))
        )
        beginner = factory.Trait(
            overhead_squat_score=factory.LazyFunction(lambda: random.randint(1, 2)),
            push_up_reps=factory.LazyFunction(lambda: random.randint(1, 10)),
            push_up_score=factory.LazyFunction(lambda: random.randint(1, 2)),
            overall_score=factory.LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))
        )
        incomplete = factory.Trait(
            push_up_reps=None,
            push_up_score=None,
            toe_touch_distance=None,
            toe_touch_score=None,
            overall_score=None
        )
        recent = factory.Trait(
            date=factory.LazyFunction(lambda: fake.date_time_this_week(tzinfo=timezone.get_current_timezone()))
        )
        old = factory.Trait(
            date=factory.LazyFunction(lambda: fake.date_time_this_year(before_now=True, after_now=False, tzinfo=timezone.get_current_timezone()))
        )


# Helper functions
def create_test_assessments(count=5, client=None, trainer=None, **kwargs):
    """
    Helper function to create multiple test assessments.
    
    Usage:
        assessments = create_test_assessments(5)  # 5 assessments with random clients/trainers
        assessments = create_test_assessments(3, client=client)  # 3 assessments for specific client
        assessments = create_test_assessments(5, trainer=trainer)  # 5 assessments by specific trainer
    """
    if client:
        kwargs['client'] = client
    if trainer:
        kwargs['trainer'] = trainer
    return AssessmentFactory.create_batch(count, **kwargs)


def create_assessment_timeline(client, trainer=None, months=6):
    """
    Create a timeline of assessments for a client over specified months.
    Returns assessments with dates spread across the timeline.
    """
    if not trainer:
        trainer = TrainerFactory()
    
    assessments = []
    for i in range(months):
        date = fake.date_time_between(
            start_date=f'-{months-i}M', 
            end_date=f'-{months-i-1}M',
            tzinfo=timezone.get_current_timezone()
        )
        assessment = AssessmentFactory(
            client=client, 
            trainer=trainer, 
            date=date
        )
        assessments.append(assessment)
    
    return assessments


def create_performance_progression(client, trainer=None, stages=3):
    """
    Create assessments showing performance progression.
    Returns assessments with improving scores over time.
    """
    if not trainer:
        trainer = TrainerFactory()
    
    assessments = []
    score_multipliers = [0.6, 0.8, 1.0]  # Progression from 60% to 100% of good scores
    
    for i, multiplier in enumerate(score_multipliers[:stages]):
        base_score = 3  # Base score of 3
        score = int(base_score * multiplier) + 1  # Ensure minimum of 1
        
        assessment = AssessmentFactory(
            client=client,
            trainer=trainer,
            date=fake.date_time_between(
                start_date=f'-{stages-i}M',
                end_date=f'-{stages-i-1}M',
                tzinfo=timezone.get_current_timezone()
            ),
            overhead_squat_score=min(score, 5),
            push_up_score=min(score, 5),
            toe_touch_score=min(score, 5),
            shoulder_mobility_score=min(score, 5),
            farmer_carry_score=min(score, 5),
            overall_score=round(score * 0.8, 1)
        )
        assessments.append(assessment)
    
    return assessments


# MCQ Model Factories
class QuestionCategoryFactory(DjangoModelFactory):
    """Factory for QuestionCategory model."""
    
    class Meta:
        model = 'assessments.QuestionCategory'
    
    name = factory.Sequence(lambda n: f"Category {n}")
    name_ko = factory.Sequence(lambda n: f"카테고리 {n}")
    description = factory.Faker('text', max_nb_chars=200)
    description_ko = factory.Faker('text', max_nb_chars=200, locale='ko_KR')
    weight = Decimal('0.15')
    order = factory.Sequence(lambda n: n)
    is_active = True


class MultipleChoiceQuestionFactory(DjangoModelFactory):
    """Factory for MultipleChoiceQuestion model."""
    
    class Meta:
        model = 'assessments.MultipleChoiceQuestion'
    
    category = factory.SubFactory(QuestionCategoryFactory)
    question_text = factory.Faker('sentence', nb_words=10)
    question_text_ko = factory.Faker('sentence', nb_words=10, locale='ko_KR')
    question_type = 'single'
    points = 10
    is_required = True
    help_text = factory.Faker('sentence')
    help_text_ko = factory.Faker('sentence', locale='ko_KR')
    order = factory.Sequence(lambda n: n)
    is_active = True


class QuestionChoiceFactory(DjangoModelFactory):
    """Factory for QuestionChoice model."""
    
    class Meta:
        model = 'assessments.QuestionChoice'
    
    question = factory.SubFactory(MultipleChoiceQuestionFactory)
    choice_text = factory.Faker('sentence', nb_words=5)
    choice_text_ko = factory.Faker('sentence', nb_words=5, locale='ko_KR')
    points = 0
    is_correct = False
    order = factory.Sequence(lambda n: n)
    contributes_to_risk = False
    risk_weight = Decimal('0.0')


class QuestionResponseFactory(DjangoModelFactory):
    """Factory for QuestionResponse model."""
    
    class Meta:
        model = 'assessments.QuestionResponse'
    
    assessment = factory.SubFactory(AssessmentFactory)
    question = factory.SubFactory(MultipleChoiceQuestionFactory)
    response_text = ""
    points_earned = 0
    
    @factory.post_generation
    def selected_choices(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Add selected choices
            for choice in extracted:
                self.selected_choices.add(choice)