# Generated by Django 5.1.3 on 2024-11-27 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_student_phone_number'),
        ('courses', '0003_alter_course_options_course_created_at'),
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='screenshot_file_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='payment',
            unique_together={('student', 'course', 'status')},
        ),
    ]
