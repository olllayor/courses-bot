from rest_framework import viewsets
from .models import StudentProgress
from .serializers import StudentProgressSerializer

class StudentProgressViewSet(viewsets.ModelViewSet):
    queryset = StudentProgress.objects.all()
    serializer_class = StudentProgressSerializer