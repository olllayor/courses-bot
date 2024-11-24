from django.db import models
from django.utils import timezone
from accounts.models import Student
from courses.models import Course

class Payment(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def confirm_payment(self):
        if self.status == self.PENDING:
            self.status = self.CONFIRMED
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False

    def cancel_payment(self):
        if self.status == self.PENDING:
            self.status = self.CANCELLED
            self.save()
            return True
        return False

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} - {self.course.title} ({self.status})"