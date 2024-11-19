from rest_framework import serializers
from .models import StudentProgress

class StudentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgress
        fields = ['id', 'student', 'lesson', 'quiz_score', 'completed_at']