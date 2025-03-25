# courses/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from mentors.models import Mentor
from decimal import Decimal
from django.core.exceptions import ValidationError


class Course(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Course price in UZS",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["-created_at"]


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    is_free = models.BooleanField(default=False)
    telegram_video_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text="Video ID from Telegram",
        verbose_name="Telegram Video ID",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["course", "id"]


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes")
    questions = models.JSONField(help_text="List of questions in JSON format")
    answers = models.JSONField(help_text="List of answer options for each question")
    correct_answers = models.JSONField(help_text="List of correct answer indices")

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    # def clean(self):
    #     """Validate that the quiz data is properly structured"""
    #     super().clean()

    #     # Check that all fields are lists
    #     if not isinstance(self.questions, list):
    #         raise ValidationError({"questions": "Questions must be a list"})

    #     if not isinstance(self.answers, list):
    #         raise ValidationError({"answers": "Answers must be a list"})

    #     if not isinstance(self.correct_answers, list):
    #         raise ValidationError({"correct_answers": "Correct answers must be a list"})

    #     # Check that the number of items matches
    #     if len(self.questions) != len(self.answers):
    #         raise ValidationError(
    #             "Number of questions must match number of answer sets"
    #         )

    #     if len(self.questions) != len(self.correct_answers):
    #         raise ValidationError(
    #             "Number of questions must match number of correct answers"
    #         )

    #     # Check that each correct answer index is valid
    #     for i, (answer_set, correct_idx) in enumerate(
    #         zip(self.answers, self.correct_answers)
    #     ):
    #         if not isinstance(answer_set, list):
    #             raise ValidationError({"answers": f"Answer set {i+1} must be a list"})

    #         if not 0 <= correct_idx < len(answer_set):
    #             raise ValidationError(
    #                 {
    #                     "correct_answers": f"Correct answer index {correct_idx} for question {i+1} is out of range"
    #                 }
    #             )
        
