# Generated by Django 5.2 on 2025-05-06 00:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_bookingline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingline',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('inprogress', 'Inprogress'), ('completed', 'Completed')], default='pending', max_length=50),
        ),
    ]
