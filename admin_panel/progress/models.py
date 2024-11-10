from django.db import models
from django.utils import timezone
from accounts.models import Student
from courses.models import Lesson
# Create your models here.


class StudentProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    quiz_score = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.student.name} - {self.lesson.title}"
    
    class Meta:
        verbose_name = 'Student Progress'
        verbose_name_plural = 'Student Progress'
        unique_together = ('student', 'lesson')