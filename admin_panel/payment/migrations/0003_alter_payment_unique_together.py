# Generated by Django 5.1.3 on 2024-12-21 22:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_student_auth_token'),
        ('courses', '0007_alter_lesson_telegram_video_id'),
        ('payment', '0002_payment_screenshot_file_id_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='payment',
            unique_together={('student', 'course')},
        ),
    ]
