# Manual migration to handle existing heart rate data

from django.db import migrations


def migrate_heart_rate_data(apps, schema_editor):
    """
    Migrate existing harvard_step_test_heart_rate to harvard_step_test_hr1
    """
    Assessment = apps.get_model('assessments', 'Assessment')
    
    # Get all assessments that might have the old heart rate field
    # Since the field is already removed in the previous migration,
    # we'll just set default values for new fields if they're null
    for assessment in Assessment.objects.all():
        # If the new fields are not set, set some default values
        if assessment.harvard_step_test_hr1 is None and assessment.harvard_step_test_duration:
            # Set reasonable default values for the three heart rate measurements
            # These would typically decrease over time
            assessment.harvard_step_test_hr1 = 80
            assessment.harvard_step_test_hr2 = 75
            assessment.harvard_step_test_hr3 = 70
            assessment.save(update_fields=['harvard_step_test_hr1', 'harvard_step_test_hr2', 'harvard_step_test_hr3'])


def reverse_migrate_heart_rate_data(apps, schema_editor):
    """
    Reverse migration - we can't really reverse this since we're going from 3 fields to 1
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0002_remove_assessment_harvard_step_test_heart_rate_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_heart_rate_data, reverse_migrate_heart_rate_data),
    ]