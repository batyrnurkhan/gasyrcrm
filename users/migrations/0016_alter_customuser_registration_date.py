# Generated by Django 5.0.4 on 2024-08-21 15:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_customuser_admission_country_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='registration_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Дата регистрации'),
        ),
    ]
