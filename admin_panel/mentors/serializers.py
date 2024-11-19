from rest_framework import serializers
from .models import Mentor, MentorAvailability

class MentorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorAvailability
        fields = ['id', 'start_time', 'end_time', 'is_available']

class MentorSerializer(serializers.ModelSerializer):
    availability = MentorAvailabilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Mentor
        fields = ['id', 'name', 'bio', 'profile_picture_id','availability']