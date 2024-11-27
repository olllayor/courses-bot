import secrets
from django.db import models
from django.utils import timezone

# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    telegram_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    auth_token = models.CharField(max_length=255, null=True, blank=True, unique=True)

    def generate_token(self):
        self.auth_token = secrets.token_hex(32)
        self.save()
        return self.auth_token

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"