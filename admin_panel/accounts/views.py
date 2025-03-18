# accounts/views.py
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Student
from .serializers import StudentSerializer

# Setup logger
logger = logging.getLogger(__name__)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer 
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter students based on query parameters"""
        queryset = Student.objects.all()
        
        # Filter by telegram_id if provided
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            queryset = queryset.filter(telegram_id=telegram_id)
            
        return queryset

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register or update a student"""
        telegram_id = request.data.get('telegram_id')
        name = request.data.get('name')
        
        if not telegram_id:
            logger.warning("register called without telegram_id")
            return Response(
                {'error': 'telegram_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not name:
            logger.warning(f"register called without name for user {telegram_id}")
            return Response(
                {'error': 'name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Check if student already exists
            try:
                student = Student.objects.get(telegram_id=telegram_id)
                logger.info(f"Updating existing student {telegram_id}")
                
                # Update name if different
                if student.name != name:
                    student.name = name
                    student.save()
                    logger.info(f"Updated name for user {telegram_id}: {name}")
                
            except Student.DoesNotExist:
                # Create new student
                logger.info(f"Creating new student with telegram_id {telegram_id}, name {name}")
                student = Student.objects.create(
                    telegram_id=telegram_id,
                    name=name
                )
            
            return Response({
                'student_id': student.id,
                'name': student.name,
                'telegram_id': student.telegram_id,
                'message': 'Student registered successfully'
            })
        except Exception as e:
            logger.error(f"Error during student registration for user {telegram_id}: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )