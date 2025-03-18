import logging

from django.db import models

# Setup logger
logger = logging.getLogger(__name__)

# Create your models here.


class Student(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    telegram_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"
        
    def validate_telegram_id(self):
        """Ensure telegram_id is valid"""
        if not self.telegram_id:
            logger.error("Empty telegram_id for student")
            return False
        return True

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
