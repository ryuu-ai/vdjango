# Generated by Django 5.2 on 2025-05-05 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_schedule_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schedule',
            name='service',
        ),
    ]
