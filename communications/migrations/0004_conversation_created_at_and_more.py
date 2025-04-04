# Generated by Django 5.1.7 on 2025-03-28 13:22

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0003_remove_conversation_created_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='participant_one',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='conversations_as_participant_one', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='participant_two',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='conversations_as_participant_two', to=settings.AUTH_USER_MODEL),
        ),
    ]
