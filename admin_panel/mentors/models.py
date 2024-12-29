from django.db import models
from django.utils import timezone

# Create your models here.


class Mentor(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    profile_picture_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Profile picture ID from Telegram",
        verbose_name="Mentor picture ID",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mentor"
        verbose_name_plural = "Mentors"


class MentorAvailability(models.Model):
    mentor = models.ForeignKey(
        Mentor, on_delete=models.CASCADE, related_name="availability"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.mentor.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} to {self.end_time.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Mentor Availability"
        verbose_name_plural = "Mentor Availability"
        ordering = ["start_time"]
