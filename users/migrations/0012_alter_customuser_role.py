# Generated by Django 5.0.4 on 2024-06-14 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(blank=True, choices=[('Anonymous', 'Anonymous'), ('Student', 'Student'), ('Teacher', 'Teacher'), ('Mentor', 'Mentor'), ('Psychologist', 'Psychologist'), ('Orientologist', 'Orientologist')], default='Anonymous', max_length=13, null=True),
        ),
    ]
