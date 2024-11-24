
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        if payment.status == Payment.PENDING:
            payment.status = Payment.CONFIRMED
            payment.confirmed_at = timezone.now()
            payment.save()
            return Response({'status': 'payment confirmed'})
        return Response({'status': 'payment already processed'}, 
                      status=status.HTTP_400_BAD_REQUEST)