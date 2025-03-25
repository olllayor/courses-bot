from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import StudentProgress
from .serializers import StudentProgressSerializer

class StudentProgressViewSet(viewsets.ModelViewSet):
    queryset = StudentProgress.objects.all()
    serializer_class = StudentProgressSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]