from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Webinar
from .serializers import WebinarSerializer

class WebinarViewSet(viewsets.ModelViewSet):
    queryset = Webinar.objects.all()
    serializer_class = WebinarSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Webinar.objects.all()
        mentor_id = self.request.query_params.get('mentor', None)
        if mentor_id is not None:
            queryset = queryset.filter(mentor_id=mentor_id)
        return queryset.order_by('-created_at')