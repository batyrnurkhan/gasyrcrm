# Generated by Django 5.0.4 on 2024-05-20 08:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0010_volunteerchannel_chat_room'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_assigned', models.DateField()),
                ('grade', models.CharField(max_length=10)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.lesson_crm2')),
                ('student', models.ForeignKey(limit_choices_to={'role': 'Student'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]