"""
Example Django data migration for Assessment model refactoring.

This demonstrates how to migrate data from the monolithic Assessment model
to the new refactored models safely and reversibly.

IMPORTANT: This is an EXAMPLE - adapt for your specific needs before use.
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
    
    print(f"Starting migration of {Assessment.objects.count()} assessments...")
    
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
                        notes=assessment.overhead_squat_notes or '',
                        knee_valgus=assessment.overhead_squat_knee_valgus or False,
                        forward_lean=assessment.overhead_squat_forward_lean or False,
                        heel_lift=assessment.overhead_squat_heel_lift or False,
                        arm_drop=getattr(assessment, 'overhead_squat_arm_drop', False),
                        quality=getattr(assessment, 'overhead_squat_quality', None),
                        score_manual_override=getattr(assessment, 'overhead_squat_score_manual_override', False)
                    )
                
                # Migrate Push-up Test
                if _has_push_up_data(assessment):
                    PushUpTest.objects.create(
                        assessment=assessment,
                        reps=assessment.push_up_reps,
                        score=assessment.push_up_score,
                        notes=assessment.push_up_notes or '',
                        push_up_type=getattr(assessment, 'push_up_type', 'standard'),
                        score_manual_override=getattr(assessment, 'push_up_score_manual_override', False)
                    )
                
                # Migrate Single Leg Balance Test
                if _has_balance_data(assessment):
                    SingleLegBalanceTest.objects.create(
                        assessment=assessment,
                        right_eyes_open=assessment.single_leg_balance_right_eyes_open,
                        left_eyes_open=assessment.single_leg_balance_left_eyes_open,
                        right_eyes_closed=assessment.single_leg_balance_right_eyes_closed,
                        left_eyes_closed=assessment.single_leg_balance_left_eyes_closed,
                        notes=assessment.single_leg_balance_notes or '',
                        score_manual=getattr(assessment, 'single_leg_balance_score_manual', None),
                        score_manual_override=getattr(assessment, 'single_leg_balance_score_manual_override', False)
                    )
                
                # Migrate Toe Touch Test
                if _has_toe_touch_data(assessment):
                    ToeTouchTest.objects.create(
                        assessment=assessment,
                        distance=assessment.toe_touch_distance,
                        score=assessment.toe_touch_score,
                        notes=assessment.toe_touch_notes or '',
                        flexibility=getattr(assessment, 'toe_touch_flexibility', None),
                        score_manual_override=getattr(assessment, 'toe_touch_score_manual_override', False)
                    )
                
                # Migrate Shoulder Mobility Test
                if _has_shoulder_mobility_data(assessment):
                    ShoulderMobilityTest.objects.create(
                        assessment=assessment,
                        right=assessment.shoulder_mobility_right,
                        left=assessment.shoulder_mobility_left,
                        score=assessment.shoulder_mobility_score,
                        notes=assessment.shoulder_mobility_notes or '',
                        pain=getattr(assessment, 'shoulder_mobility_pain', False),
                        asymmetry=getattr(assessment, 'shoulder_mobility_asymmetry', None),
                        category=getattr(assessment, 'shoulder_mobility_category', None),
                        score_manual_override=getattr(assessment, 'shoulder_mobility_score_manual_override', False)
                    )
                
                # Migrate Farmer's Carry Test
                if _has_farmers_carry_data(assessment):
                    FarmersCarryTest.objects.create(
                        assessment=assessment,
                        weight=assessment.farmer_carry_weight,
                        distance=assessment.farmer_carry_distance,
                        time=assessment.farmer_carry_time,
                        score=assessment.farmer_carry_score,
                        notes=assessment.farmer_carry_notes or '',
                        percentage=getattr(assessment, 'farmer_carry_percentage', None),
                        score_manual_override=getattr(assessment, 'farmer_carry_score_manual_override', False)
                    )
                
                # Migrate Harvard Step Test
                if _has_harvard_step_data(assessment):
                    HarvardStepTest.objects.create(
                        assessment=assessment,
                        hr1=assessment.harvard_step_test_hr1,
                        hr2=assessment.harvard_step_test_hr2,
                        hr3=assessment.harvard_step_test_hr3,
                        duration=getattr(assessment, 'harvard_step_test_duration', None),
                        notes=assessment.harvard_step_test_notes or '',
                        score_manual=getattr(assessment, 'harvard_step_test_score_manual', None),
                        score_manual_override=getattr(assessment, 'harvard_step_test_score_manual_override', False)
                    )
                
                # Migrate Manual Overrides
                override_data = _collect_manual_overrides(assessment)
                if override_data:
                    ManualScoreOverride.objects.create(
                        assessment=assessment,
                        overrides=override_data,
                        modified_by_id=assessment.trainer.user.id if assessment.trainer else None
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
    """
    # Get model classes
    Assessment = apps.get_model('assessments', 'Assessment')
    OverheadSquatTest = apps.get_model('assessments', 'OverheadSquatTest')
    PushUpTest = apps.get_model('assessments', 'PushUpTest')
    # ... other models
    
    print("Starting reverse migration...")
    
    for assessment in Assessment.objects.all():
        try:
            with transaction.atomic():
                # Restore Overhead Squat data
                if hasattr(assessment, 'overhead_squat'):
                    squat = assessment.overhead_squat
                    assessment.overhead_squat_score = squat.score
                    assessment.overhead_squat_notes = squat.notes
                    assessment.overhead_squat_knee_valgus = squat.knee_valgus
                    assessment.overhead_squat_forward_lean = squat.forward_lean
                    assessment.overhead_squat_heel_lift = squat.heel_lift
                    # Continue for other fields...
                
                # Restore other test data...
                
                assessment.save()
                
        except Exception as e:
            print(f"Error in reverse migration for assessment {assessment.id}: {str(e)}")
    
    print("Reverse migration complete")


# Helper functions for data validation
def _has_overhead_squat_data(assessment):
    """Check if assessment has overhead squat data worth migrating."""
    return any([
        assessment.overhead_squat_score is not None,
        assessment.overhead_squat_knee_valgus,
        assessment.overhead_squat_forward_lean,
        assessment.overhead_squat_heel_lift,
        getattr(assessment, 'overhead_squat_arm_drop', False),
        assessment.overhead_squat_notes
    ])


def _has_push_up_data(assessment):
    """Check if assessment has push-up data worth migrating."""
    return any([
        assessment.push_up_reps is not None,
        assessment.push_up_score is not None,
        assessment.push_up_notes
    ])


def _has_balance_data(assessment):
    """Check if assessment has balance data worth migrating."""
    return any([
        assessment.single_leg_balance_right_eyes_open is not None,
        assessment.single_leg_balance_left_eyes_open is not None,
        assessment.single_leg_balance_right_eyes_closed is not None,
        assessment.single_leg_balance_left_eyes_closed is not None,
        assessment.single_leg_balance_notes
    ])


def _has_toe_touch_data(assessment):
    """Check if assessment has toe touch data worth migrating."""
    return any([
        assessment.toe_touch_distance is not None,
        assessment.toe_touch_score is not None,
        assessment.toe_touch_notes
    ])


def _has_shoulder_mobility_data(assessment):
    """Check if assessment has shoulder mobility data worth migrating."""
    return any([
        assessment.shoulder_mobility_right is not None,
        assessment.shoulder_mobility_left is not None,
        assessment.shoulder_mobility_score is not None,
        assessment.shoulder_mobility_notes
    ])


def _has_farmers_carry_data(assessment):
    """Check if assessment has farmer's carry data worth migrating."""
    return any([
        assessment.farmer_carry_weight is not None,
        assessment.farmer_carry_distance is not None,
        assessment.farmer_carry_time is not None,
        assessment.farmer_carry_score is not None,
        assessment.farmer_carry_notes
    ])


def _has_harvard_step_data(assessment):
    """Check if assessment has Harvard step test data worth migrating."""
    return any([
        assessment.harvard_step_test_hr1 is not None,
        assessment.harvard_step_test_hr2 is not None,
        assessment.harvard_step_test_hr3 is not None,
        assessment.harvard_step_test_notes
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
                    'timestamp': assessment.created_at.isoformat(),
                    'user_id': assessment.trainer.user.id if assessment.trainer else None
                }
    
    return overrides if overrides else None


class Migration(migrations.Migration):
    """
    Django migration class for Assessment model refactoring.
    """
    
    dependencies = [
        ('assessments', '0013_add_refactored_models'),  # Previous migration that added new models
    ]
    
    operations = [
        migrations.RunPython(
            migrate_assessment_data_forward,
            migrate_assessment_data_reverse,
            atomic=False  # Handle transactions manually for better error recovery
        ),
    ]


# Validation script to run after migration
def validate_migration():
    """
    Validation script to ensure data migration was successful.
    Run this after migration to verify data integrity.
    """
    from apps.assessments.models import Assessment
    from apps.assessments.refactored_models import (
        OverheadSquatTest, PushUpTest, SingleLegBalanceTest
    )
    
    print("Validating migration...")
    
    total_assessments = Assessment.objects.count()
    migrated_tests = {
        'overhead_squat': OverheadSquatTest.objects.count(),
        'push_up': PushUpTest.objects.count(),
        'single_leg_balance': SingleLegBalanceTest.objects.count(),
        # Add other test types...
    }
    
    print(f"Total assessments: {total_assessments}")
    for test_type, count in migrated_tests.items():
        print(f"Migrated {test_type} tests: {count}")
    
    # Sample validation - check score consistency
    sample_assessments = Assessment.objects.filter(
        overhead_squat_score__isnull=False
    )[:10]
    
    validation_errors = 0
    for assessment in sample_assessments:
        if hasattr(assessment, 'overhead_squat'):
            old_score = assessment.overhead_squat_score
            new_score = assessment.overhead_squat.score
            if old_score != new_score:
                print(f"Score mismatch for assessment {assessment.id}: {old_score} != {new_score}")
                validation_errors += 1
    
    if validation_errors == 0:
        print("✅ Validation passed - no score mismatches found")
    else:
        print(f"❌ Validation failed - {validation_errors} score mismatches found")
    
    print("Validation complete")


if __name__ == '__main__':
    # Can be run as a standalone script for testing
    print("This is an example migration script.")
    print("Adapt the migration code for your specific Django migration file.")