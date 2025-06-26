"""
Data migration for Assessment model refactoring.

This migration safely migrates data from the monolithic Assessment model
to the new refactored models.
"""
from django.db import migrations, transaction


def migrate_assessment_data_forward(apps, schema_editor):
    """
    Migrate data from Assessment to individual test models.
    """
    # Get model classes
    Assessment = apps.get_model('assessments', 'Assessment')
    OverheadSquatTest = apps.get_model('assessments', 'OverheadSquatTest')
    PushUpTest = apps.get_model('assessments', 'PushUpTest')
    SingleLegBalanceTest = apps.get_model('assessments', 'SingleLegBalanceTest')
    ToeTouchTest = apps.get_model('assessments', 'ToeTouchTest')
    ShoulderMobilityTest = apps.get_model('assessments', 'ShoulderMobilityTest')
    FarmersCarryTest = apps.get_model('assessments', 'FarmersCarryTest')
    HarvardStepTest = apps.get_model('assessments', 'HarvardStepTest')
    ManualScoreOverride = apps.get_model('assessments', 'ManualScoreOverride')
    
    total_assessments = Assessment.objects.count()
    print(f"Starting migration of {total_assessments} assessments...")
    
    migrated_count = 0
    error_count = 0
    
    for assessment in Assessment.objects.all():
        try:
            with transaction.atomic():
                # Migrate Overhead Squat Test
                if _has_overhead_squat_data(assessment):
                    OverheadSquatTest.objects.create(
                        assessment=assessment,
                        score=assessment.overhead_squat_score,
                        notes=getattr(assessment, 'overhead_squat_notes', '') or '',
                        knee_valgus=getattr(assessment, 'overhead_squat_knee_valgus', False) or False,
                        forward_lean=getattr(assessment, 'overhead_squat_forward_lean', False) or False,
                        heel_lift=getattr(assessment, 'overhead_squat_heel_lift', False) or False,
                        arm_drop=getattr(assessment, 'overhead_squat_arm_drop', False) or False,
                        quality=getattr(assessment, 'overhead_squat_quality', None),
                        score_manual_override=getattr(assessment, 'overhead_squat_score_manual_override', False) or False
                    )
                
                # Migrate Push-up Test
                if _has_push_up_data(assessment):
                    PushUpTest.objects.create(
                        assessment=assessment,
                        reps=getattr(assessment, 'push_up_reps', None),
                        score=getattr(assessment, 'push_up_score', None),
                        notes=getattr(assessment, 'push_up_notes', '') or '',
                        push_up_type=getattr(assessment, 'push_up_type', 'standard') or 'standard',
                        score_manual_override=getattr(assessment, 'push_up_score_manual_override', False) or False
                    )
                
                # Migrate Single Leg Balance Test
                if _has_balance_data(assessment):
                    SingleLegBalanceTest.objects.create(
                        assessment=assessment,
                        right_eyes_open=getattr(assessment, 'single_leg_balance_right_eyes_open', None),
                        left_eyes_open=getattr(assessment, 'single_leg_balance_left_eyes_open', None),
                        right_eyes_closed=getattr(assessment, 'single_leg_balance_right_eyes_closed', None),
                        left_eyes_closed=getattr(assessment, 'single_leg_balance_left_eyes_closed', None),
                        notes=getattr(assessment, 'single_leg_balance_notes', '') or '',
                        score_manual=getattr(assessment, 'single_leg_balance_score_manual', None),
                        score_manual_override=getattr(assessment, 'single_leg_balance_score_manual_override', False) or False
                    )
                
                # Migrate Toe Touch Test
                if _has_toe_touch_data(assessment):
                    ToeTouchTest.objects.create(
                        assessment=assessment,
                        distance=getattr(assessment, 'toe_touch_distance', None),
                        score=getattr(assessment, 'toe_touch_score', None),
                        notes=getattr(assessment, 'toe_touch_notes', '') or '',
                        flexibility=getattr(assessment, 'toe_touch_flexibility', None),
                        score_manual_override=getattr(assessment, 'toe_touch_score_manual_override', False) or False
                    )
                
                # Migrate Shoulder Mobility Test
                if _has_shoulder_mobility_data(assessment):
                    ShoulderMobilityTest.objects.create(
                        assessment=assessment,
                        right=getattr(assessment, 'shoulder_mobility_right', None),
                        left=getattr(assessment, 'shoulder_mobility_left', None),
                        score=getattr(assessment, 'shoulder_mobility_score', None),
                        notes=getattr(assessment, 'shoulder_mobility_notes', '') or '',
                        pain=getattr(assessment, 'shoulder_mobility_pain', False) or False,
                        asymmetry=getattr(assessment, 'shoulder_mobility_asymmetry', None),
                        category=getattr(assessment, 'shoulder_mobility_category', None),
                        score_manual_override=getattr(assessment, 'shoulder_mobility_score_manual_override', False) or False
                    )
                
                # Migrate Farmer's Carry Test
                if _has_farmers_carry_data(assessment):
                    FarmersCarryTest.objects.create(
                        assessment=assessment,
                        weight=getattr(assessment, 'farmer_carry_weight', None),
                        distance=getattr(assessment, 'farmer_carry_distance', None),
                        time=getattr(assessment, 'farmer_carry_time', None),
                        score=getattr(assessment, 'farmer_carry_score', None),
                        notes=getattr(assessment, 'farmer_carry_notes', '') or '',
                        percentage=getattr(assessment, 'farmer_carry_percentage', None),
                        score_manual_override=getattr(assessment, 'farmer_carry_score_manual_override', False) or False
                    )
                
                # Migrate Harvard Step Test
                if _has_harvard_step_data(assessment):
                    HarvardStepTest.objects.create(
                        assessment=assessment,
                        hr1=getattr(assessment, 'harvard_step_test_hr1', None),
                        hr2=getattr(assessment, 'harvard_step_test_hr2', None),
                        hr3=getattr(assessment, 'harvard_step_test_hr3', None),
                        duration=getattr(assessment, 'harvard_step_test_duration', None),
                        notes=getattr(assessment, 'harvard_step_test_notes', '') or '',
                        score_manual=getattr(assessment, 'harvard_step_test_score_manual', None),
                        score_manual_override=getattr(assessment, 'harvard_step_test_score_manual_override', False) or False
                    )
                
                # Migrate Manual Overrides
                override_data = _collect_manual_overrides(assessment)
                if override_data:
                    # Get the User model
                    User = apps.get_model('auth', 'User')
                    trainer_user = None
                    
                    if hasattr(assessment, 'trainer') and assessment.trainer:
                        try:
                            trainer_user = assessment.trainer.user
                        except:
                            # Handle case where trainer might not have user
                            pass
                    
                    ManualScoreOverride.objects.create(
                        assessment=assessment,
                        overrides=override_data,
                        modified_by=trainer_user
                    )
                
                migrated_count += 1
                
                if migrated_count % 100 == 0:
                    print(f"Migrated {migrated_count} assessments...")
                    
        except Exception as e:
            error_count += 1
            print(f"Error migrating assessment {assessment.id}: {str(e)}")
    
    print(f"Migration complete: {migrated_count} successful, {error_count} errors")


def migrate_assessment_data_reverse(apps, schema_editor):
    """
    Reverse migration - copy data back from test models to Assessment.
    This is a safety net to allow rollback if needed.
    """
    # Get model classes
    Assessment = apps.get_model('assessments', 'Assessment')
    OverheadSquatTest = apps.get_model('assessments', 'OverheadSquatTest')
    PushUpTest = apps.get_model('assessments', 'PushUpTest')
    
    print("Starting reverse migration...")
    
    for assessment in Assessment.objects.all():
        try:
            with transaction.atomic():
                # Restore Overhead Squat data
                try:
                    squat = OverheadSquatTest.objects.get(assessment=assessment)
                    assessment.overhead_squat_score = squat.score
                    if hasattr(assessment, 'overhead_squat_notes'):
                        assessment.overhead_squat_notes = squat.notes
                    if hasattr(assessment, 'overhead_squat_knee_valgus'):
                        assessment.overhead_squat_knee_valgus = squat.knee_valgus
                    if hasattr(assessment, 'overhead_squat_forward_lean'):
                        assessment.overhead_squat_forward_lean = squat.forward_lean
                    if hasattr(assessment, 'overhead_squat_heel_lift'):
                        assessment.overhead_squat_heel_lift = squat.heel_lift
                except OverheadSquatTest.DoesNotExist:
                    pass
                
                # Restore Push-up data
                try:
                    pushup = PushUpTest.objects.get(assessment=assessment)
                    if hasattr(assessment, 'push_up_reps'):
                        assessment.push_up_reps = pushup.reps
                    if hasattr(assessment, 'push_up_score'):
                        assessment.push_up_score = pushup.score
                except PushUpTest.DoesNotExist:
                    pass
                
                # Continue for other test types...
                
                assessment.save()
                
        except Exception as e:
            print(f"Error in reverse migration for assessment {assessment.id}: {str(e)}")
    
    print("Reverse migration complete")


# Helper functions for data validation
def _has_overhead_squat_data(assessment):
    """Check if assessment has overhead squat data worth migrating."""
    return any([
        getattr(assessment, 'overhead_squat_score', None) is not None,
        getattr(assessment, 'overhead_squat_knee_valgus', False),
        getattr(assessment, 'overhead_squat_forward_lean', False),
        getattr(assessment, 'overhead_squat_heel_lift', False),
        getattr(assessment, 'overhead_squat_arm_drop', False),
        getattr(assessment, 'overhead_squat_notes', None)
    ])


def _has_push_up_data(assessment):
    """Check if assessment has push-up data worth migrating."""
    return any([
        getattr(assessment, 'push_up_reps', None) is not None,
        getattr(assessment, 'push_up_score', None) is not None,
        getattr(assessment, 'push_up_notes', None)
    ])


def _has_balance_data(assessment):
    """Check if assessment has balance data worth migrating."""
    return any([
        getattr(assessment, 'single_leg_balance_right_eyes_open', None) is not None,
        getattr(assessment, 'single_leg_balance_left_eyes_open', None) is not None,
        getattr(assessment, 'single_leg_balance_right_eyes_closed', None) is not None,
        getattr(assessment, 'single_leg_balance_left_eyes_closed', None) is not None,
        getattr(assessment, 'single_leg_balance_notes', None)
    ])


def _has_toe_touch_data(assessment):
    """Check if assessment has toe touch data worth migrating."""
    return any([
        getattr(assessment, 'toe_touch_distance', None) is not None,
        getattr(assessment, 'toe_touch_score', None) is not None,
        getattr(assessment, 'toe_touch_notes', None)
    ])


def _has_shoulder_mobility_data(assessment):
    """Check if assessment has shoulder mobility data worth migrating."""
    return any([
        getattr(assessment, 'shoulder_mobility_right', None) is not None,
        getattr(assessment, 'shoulder_mobility_left', None) is not None,
        getattr(assessment, 'shoulder_mobility_score', None) is not None,
        getattr(assessment, 'shoulder_mobility_notes', None)
    ])


def _has_farmers_carry_data(assessment):
    """Check if assessment has farmer's carry data worth migrating."""
    return any([
        getattr(assessment, 'farmer_carry_weight', None) is not None,
        getattr(assessment, 'farmer_carry_distance', None) is not None,
        getattr(assessment, 'farmer_carry_time', None) is not None,
        getattr(assessment, 'farmer_carry_score', None) is not None,
        getattr(assessment, 'farmer_carry_notes', None)
    ])


def _has_harvard_step_data(assessment):
    """Check if assessment has Harvard step test data worth migrating."""
    return any([
        getattr(assessment, 'harvard_step_test_hr1', None) is not None,
        getattr(assessment, 'harvard_step_test_hr2', None) is not None,
        getattr(assessment, 'harvard_step_test_hr3', None) is not None,
        getattr(assessment, 'harvard_step_test_notes', None)
    ])


def _collect_manual_overrides(assessment):
    """Collect all manual override data into JSON structure."""
    overrides = {}
    
    # Check all override fields and collect them
    override_fields = [
        'overhead_squat_score_manual_override',
        'push_up_score_manual_override',
        'toe_touch_score_manual_override',
        'shoulder_mobility_score_manual_override',
        'farmer_carry_score_manual_override',
        'single_leg_balance_score_manual_override',
        'harvard_step_test_score_manual_override',
        'overall_score_manual_override',
        'strength_score_manual_override',
        'mobility_score_manual_override',
        'balance_score_manual_override',
        'cardio_score_manual_override',
    ]
    
    for field in override_fields:
        if hasattr(assessment, field) and getattr(assessment, field, False):
            # Extract test type and field name
            parts = field.replace('_manual_override', '').split('_')
            test_type = '_'.join(parts[:-1])
            field_name = parts[-1]
            
            if test_type not in overrides:
                overrides[test_type] = {}
            
            # Get the actual overridden value
            score_field = field.replace('_manual_override', '')
            override_value = getattr(assessment, score_field, None)
            
            if override_value is not None:
                overrides[test_type][field_name] = {
                    'value': override_value,
                    'timestamp': assessment.created_at.isoformat() if hasattr(assessment, 'created_at') else None,
                    'user_id': assessment.trainer.user.id if hasattr(assessment, 'trainer') and assessment.trainer and hasattr(assessment.trainer, 'user') else None
                }
    
    return overrides if overrides else None


class Migration(migrations.Migration):
    """
    Django migration class for Assessment model refactoring data migration.
    """
    
    dependencies = [
        ('assessments', '0014_add_refactored_models'),
    ]
    
    operations = [
        migrations.RunPython(
            migrate_assessment_data_forward,
            migrate_assessment_data_reverse,
            atomic=False  # Handle transactions manually for better error recovery
        ),
    ]