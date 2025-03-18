# admin_panel/mentors/views.py
import logging

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Mentor, MentorAvailability
from .serializers import MentorAvailabilitySerializer, MentorSerializer

logger = logging.getLogger(__name__)

class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        logger.info(f"Listing mentors, telegram_id: {request.query_params.get('telegram_id')}")
        return super().list(request, *args, **kwargs)
        
    def retrieve(self, request, *args, **kwargs):
        logger.info(f"Retrieving mentor, telegram_id: {request.query_params.get('telegram_id')}")
        return super().retrieve(request, *args, **kwargs)

class MentorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = MentorAvailability.objects.all()
    serializer_class = MentorAvailabilitySerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access
    
    def get_permissions(self):
        """Always allow unauthenticated access for listing and retrieval"""
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]