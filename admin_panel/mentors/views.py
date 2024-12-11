# admin_panel/mentors/views.py
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Mentor, MentorAvailability
from .serializers import MentorSerializer, MentorAvailabilitySerializer
import logging 

logger = logging.getLogger(__name__)

class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class MentorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = MentorAvailability.objects.all()
    serializer_class = MentorAvailabilitySerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access