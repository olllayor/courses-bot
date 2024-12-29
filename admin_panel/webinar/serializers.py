from rest_framework import serializers
from .models import Webinar
from mentors.serializers import MentorSerializer

class WebinarSerializer(serializers.ModelSerializer):
    mentor_details = MentorSerializer(source='mentor', read_only=True)

    class Meta:
        model = Webinar
        fields = ['id', 'mentor', 'mentor_details', 'title', 
                 'video_telegram_id', 'created_at']
        read_only_fields = ['created_at']