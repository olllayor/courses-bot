# courses/views.py
import logging

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Course, Lesson, Quiz
from .serializers import CourseSerializer, LessonSerializer, QuizSerializer

logger = logging.getLogger(__name__)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
        
    def list(self, request, *args, **kwargs):
        logger.info(f"Listing courses, telegram_id: {request.query_params.get('telegram_id')}")
        return super().list(request, *args, **kwargs)
        
    def retrieve(self, request, *args, **kwargs):
        logger.info(f"Retrieving course, telegram_id: {request.query_params.get('telegram_id')}")
        return super().retrieve(request, *args, **kwargs)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]