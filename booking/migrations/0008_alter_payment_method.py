# Generated by Django 5.2 on 2025-05-06 02:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_alter_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[('gcash', 'GCash'), ('paypal', 'PayPal')], max_length=50),
        ),
    ]
