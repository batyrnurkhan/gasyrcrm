# Generated by Django 5.0.4 on 2024-05-30 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_message_file_alter_message_message'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['timestamp']},
        ),
        migrations.AddField(
            model_name='message',
            name='message_type',
            field=models.CharField(choices=[('message', 'Message'), ('conf', 'Conference'), ('task', 'Task')], default='message', max_length=10),
        ),
    ]