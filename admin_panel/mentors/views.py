from rest_framework import viewsets
from .models import Mentor, MentorAvailability
from .serializers import MentorSerializer, MentorAvailabilitySerializer

class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer

class MentorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = MentorAvailability.objects.all()
    serializer_class = MentorAvailabilitySerializer