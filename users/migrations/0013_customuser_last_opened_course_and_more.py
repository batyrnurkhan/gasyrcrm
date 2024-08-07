# Generated by Django 5.0.4 on 2024-07-03 04:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_course_published'),
        ('users', '0012_alter_customuser_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='last_opened_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.course'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_opened_course_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
