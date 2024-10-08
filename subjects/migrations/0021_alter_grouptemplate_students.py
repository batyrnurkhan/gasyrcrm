# Generated by Django 5.0.4 on 2024-06-28 03:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0020_lesson_crm2_students_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouptemplate',
            name='students',
            field=models.ManyToManyField(limit_choices_to={'role': 'Student'}, related_name='group_template', to=settings.AUTH_USER_MODEL),
        ),
    ]
