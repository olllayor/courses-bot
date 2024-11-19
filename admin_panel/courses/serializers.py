from rest_framework import serializers
from .models import Course, Lesson, Quiz

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'questions', 'answers']

class LessonSerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'is_free', 'telegram_video_id', 'quizzes']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'mentor', 'lessons']