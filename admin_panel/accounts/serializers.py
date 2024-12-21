from rest_framework import serializers
from .models import Student
from courses.models import Course


class StudentSerializer(serializers.ModelSerializer):
    purchased_courses = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ["id", "name", "telegram_id", "phone_number", "purchased_courses"]

    def get_purchased_courses(self, obj):
        confirmed_payments = obj.payments.filter(status="confirmed")
        return [
            {
                "id": payment.course.id,
                "title": payment.course.title,
                "purchased_at": payment.confirmed_at,
            }
            for payment in confirmed_payments
        ]
