# subjects/migrations/0018_auto_20240610_1010.py

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0017_achievement_studentachievement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentachievement',
            name='awarded_date',
        ),
        migrations.AddField(
            model_name='studentachievement',
            name='awarded_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='studentachievement',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
