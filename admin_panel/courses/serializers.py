from rest_framework import serializers
from .models import Course, Lesson, Quiz

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'lesson', 'questions', 'answers']

class LessonSerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'content', 'is_free',
                 'telegram_video_id', 'created_at', 'updated_at', 
                 'quizzes']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'mentor', 'title', 'description', 'price',
                 'lessons', 'total_students']

    def get_total_students(self, obj):
        return obj.payments.filter(status='confirmed').count()