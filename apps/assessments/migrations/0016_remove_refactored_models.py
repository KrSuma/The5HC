# Generated manually to remove refactored models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0015_migrate_to_refactored_models'),
    ]

    operations = [
        # Remove all the refactored model tables
        migrations.DeleteModel(
            name='FarmersCarryTest',
        ),
        migrations.DeleteModel(
            name='HarvardStepTest',
        ),
        migrations.DeleteModel(
            name='OverheadSquatTest',
        ),
        migrations.DeleteModel(
            name='PushUpTest',
        ),
        migrations.DeleteModel(
            name='ShoulderMobilityTest',
        ),
        migrations.DeleteModel(
            name='SingleLegBalanceTest',
        ),
        migrations.DeleteModel(
            name='ToeTouchTest',
        ),
    ]