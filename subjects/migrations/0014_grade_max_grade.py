# Generated by Django 5.0.4 on 2024-06-10 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0013_lesson_crm2_google_meet_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='grade',
            name='max_grade',
            field=models.IntegerField(default=1100),
            preserve_default=False,
        ),
    ]
