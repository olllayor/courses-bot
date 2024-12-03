# accounts/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Student
from .serializers import StudentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def authenticate(self, request):
        telegram_id = request.data.get('telegram_id')
        name = request.data.get('name')
        
        if not telegram_id:
            return Response({'error': 'telegram_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        student, created = Student.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={'name': name}
        )
        
        if not student.auth_token:
            student.generate_token()
            
        return Response({
            'token': student.auth_token,
            'student_id': student.id
        })