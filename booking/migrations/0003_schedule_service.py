# Generated by Django 5.2 on 2025-05-05 13:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_rename_end_time_schedule_available_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='booking.service'),
        ),
    ]
