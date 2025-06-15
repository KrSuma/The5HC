from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ('trainers', '0002_create_initial_trainer_profiles'),
    ]
    
    operations = [
        migrations.AddIndex(
            model_name='trainer',
            index=models.Index(fields=['organization', 'is_active'], name='trainers_tr_organiz_8e0c25_idx'),
        ),
        migrations.AddIndex(
            model_name='trainer',
            index=models.Index(fields=['user'], name='trainers_tr_user_id_7a9e8f_idx'),
        ),
        migrations.AddIndex(
            model_name='trainer',
            index=models.Index(fields=['role'], name='trainers_tr_role_3f2d9a_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['slug'], name='trainers_or_slug_6a8c1b_idx'),
        ),
        migrations.AddIndex(
            model_name='trainerinvitation',
            index=models.Index(fields=['organization', 'status'], name='trainers_tr_organiz_4e7b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='trainerinvitation',
            index=models.Index(fields=['invitation_code'], name='trainers_tr_invitat_9d2f5e_idx'),
        ),
        migrations.AddIndex(
            model_name='trainerinvitation',
            index=models.Index(fields=['email', 'status'], name='trainers_tr_email_7c8a2d_idx'),
        ),
    ]