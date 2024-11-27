# payments/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Payment(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    screenshot_file_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        unique_together = ['student', 'course', 'status']

    def clean(self):
        if self.amount != self.course.price:
            raise ValidationError("Payment amount must match course price")
        
        if Payment.objects.filter(
            student=self.student,
            course=self.course,
            status=self.CONFIRMED
        ).exists():
            raise ValidationError("Course already purchased")

    def confirm_payment(self):
        if self.status != self.PENDING:
            return False
        self.status = self.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()
        return True

    def cancel_payment(self):
        if self.status != self.PENDING:
            return False
        self.status = self.CANCELLED
        self.save()
        return True