# courses/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from mentors.models import Mentor

class Course(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=0.00,  # Add default value
        validators=[MinValueValidator(0)],
        help_text="Course price in UZS"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    is_free = models.BooleanField(default=False)
    telegram_video_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text="Video ID from Telegram",
        verbose_name="Telegram Video ID"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['course', 'id']

class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')
    questions = models.JSONField()
    answers = models.JSONField()

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'