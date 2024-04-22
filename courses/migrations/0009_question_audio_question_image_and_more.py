# Generated by Django 5.0.4 on 2024-04-19 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_testsubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='question_audio/'),
        ),
        migrations.AddField(
            model_name='question',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='question_images/'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('SC', 'Single Choice'), ('MC', 'Multiple Choice'), ('IMG', 'Image Based'), ('AUD', 'Audio Based')], default='SC', max_length=3),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]