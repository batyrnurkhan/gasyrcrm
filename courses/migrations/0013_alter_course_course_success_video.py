# Generated by Django 5.0.4 on 2024-05-20 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0012_testsubmission_selected_answers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='course_success_video',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]