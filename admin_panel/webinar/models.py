from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from mentors.models import Mentor

class Webinar(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="webinars")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_telegram_id = models.CharField(
        max_length=255,
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9_-]+$',
            message='Video ID must be alphanumeric'
        )]
    )
    duration = models.PositiveIntegerField(help_text="Duration in minutes", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    @property
    def is_completed(self):
        return self.status == 'completed'

    class Meta:
        verbose_name = "Webinar"
        verbose_name_plural = "Webinars"
        ordering = ["-created_at"]