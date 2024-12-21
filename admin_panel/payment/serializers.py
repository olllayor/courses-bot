
from rest_framework import serializers
from .models import Payment
from courses.serializers import CourseSerializer
from accounts.serializers import StudentSerializer

class PaymentSerializer(serializers.ModelSerializer):
    course_details = CourseSerializer(source='course', read_only=True)
    student_details = StudentSerializer(source='student', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'student', 'course', 'amount', 'status', 
                 'created_at', 'confirmed_at', 'course_details', 
                 'student_details', 'screenshot_file_id']
        read_only_fields = ['confirmed_at']