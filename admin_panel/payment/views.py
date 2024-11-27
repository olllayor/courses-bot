# payments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Payment

from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()  # Add this line
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(student__user=self.request.user)

    @action(detail=True, methods=['POST'])
    def confirm(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        payment = self.get_object()
        if payment.confirm_payment():
            return Response({'status': 'confirmed'})
        return Response(
            {'error': 'Payment cannot be confirmed'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        payment = self.get_object()
        if payment.cancel_payment():
            return Response({'status': 'cancelled'})
        return Response(
            {'error': 'Payment cannot be cancelled'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['PUT'])
    def save_screenshot(self, request, pk=None):
        payment = self.get_object()
        file_id = request.data.get('file_id')
        
        if not file_id:
            return Response(
                {'error': 'No file_id provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.screenshot_file_id = file_id
        payment.save()
        return Response({'status': 'screenshot saved'})