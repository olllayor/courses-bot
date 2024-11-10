from django.db import models

# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"