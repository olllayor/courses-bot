import secrets
from django.db import models
from django.utils import timezone
import os
# Create your models here.


class Student(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    telegram_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add this field

    auth_token = models.CharField(max_length=255, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)

    def generate_token(self):
        """Generate and save auth token"""
        self.auth_token = secrets.token_hex(32)
        self.token_created_at = timezone.now()
        self.save()
        return self.auth_token

    def refresh_token(self):
        """Refresh existing token"""
        return self.generate_token()

    def is_token_valid(self):
        """Check if token is still valid (within 24 hours)"""
        if not self.token_created_at:
            return False
        return timezone.now() < self.token_created_at + timezone.timedelta(hours=24)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
