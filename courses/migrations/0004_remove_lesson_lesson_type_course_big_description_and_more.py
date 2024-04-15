# Generated by Django 5.0.4 on 2024-04-11 10:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_course_created_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lesson',
            name='lesson_type',
        ),
        migrations.AddField(
            model_name='course',
            name='big_description',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course',
            name='course_difficulty',
            field=models.IntegerField(choices=[(1, 'Very Easy'), (2, 'Easy'), (3, 'Medium'), (4, 'Hard'), (5, 'Very Hard')], default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course',
            name='course_picture',
            field=models.ImageField(default=1, upload_to='course_pictures/'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course',
            name='course_time',
            field=models.PositiveIntegerField(default=1, help_text='Duration in hours'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course',
            name='full_description',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='course',
            name='mini_description',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lesson',
            name='module',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.module'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='module',
            name='course',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='courses.course'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='module',
            name='module_test',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='lesson_test',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='lessonliterature',
            name='lesson',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='literatures', to='courses.lesson'),
        ),
    ]