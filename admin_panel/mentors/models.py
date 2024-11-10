from django.db import models

# Create your models here.

class Mentor(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mentor"
        verbose_name_plural = "Mentors"

        
