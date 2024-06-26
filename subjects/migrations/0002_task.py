# Generated by Django 5.0.4 on 2024-05-14 11:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_message_file_alter_message_message'),
        ('subjects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('deadline', models.DateTimeField()),
                ('file', models.FileField(blank=True, null=True, upload_to='task_files/')),
                ('chat_room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='chats.chatroom')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_tasks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
