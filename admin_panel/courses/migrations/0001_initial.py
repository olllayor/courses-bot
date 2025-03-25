from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.utils.timezone
from django.core.validators import MinValueValidator

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mentors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Course price in UZS', max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='mentors.mentor')),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True, null=True)),
                ('is_free', models.BooleanField(default=False)),
                ('telegram_video_id', models.CharField(help_text='Video ID from Telegram', max_length=255, verbose_name='Telegram Video ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.course')),
            ],
            options={
                'verbose_name': 'Lesson',
                'verbose_name_plural': 'Lessons',
                'ordering': ['course', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questions', models.JSONField(help_text='List of questions in JSON format')),
                ('answers', models.JSONField(help_text='List of answer options for each question')),
                ('correct_answers', models.JSONField(help_text='List of correct answer indices')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.lesson')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
            },
        ),
    ]