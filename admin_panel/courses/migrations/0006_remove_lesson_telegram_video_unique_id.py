# Generated by Django 5.1.3 on 2024-12-18 23:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_lesson_telegram_video_unique_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lesson',
            name='telegram_video_unique_id',
        ),
    ]
