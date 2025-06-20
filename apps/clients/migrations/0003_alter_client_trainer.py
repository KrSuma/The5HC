# Generated by Django 5.0.1 on 2025-06-15 08:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_alter_client_age_alter_client_email_and_more'),
        ('trainers', '0004_auditlog_notification_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='trainer',
            field=models.ForeignKey(help_text='The trainer managing this client', on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='trainers.trainer', verbose_name='Trainer'),
        ),
    ]
