# payments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from accounts.models import Student
from payment.models import Payment
from payment.serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter payments based on user role and parameters"""
        queryset = Payment.objects.all()
        
        if self.request.user.is_staff:
            return queryset

        # Get student by auth token
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            try:
                student = Student.objects.get(telegram_id=telegram_id)
                return queryset.filter(student=student)
            except Student.DoesNotExist:
                return Payment.objects.none()
                
        return Payment.objects.none()

    def create(self, request, *args, **kwargs):
        """Create payment with proper student association"""
        try:
            # Get student by telegram_id
            telegram_id = request.data.get('student')
            student = Student.objects.get(telegram_id=telegram_id)
            
            # Create payment data
            payment_data = {
                'student': student.id,
                'course': request.data.get('course'),
                'amount': request.data.get('amount'),
                'status': Payment.PENDING
            }
            
            serializer = self.get_serializer(data=payment_data)
            serializer.is_valid(raise_for_exception=True)
            self.perform_create(serializer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["PUT"])
    def save_screenshot(self, request, pk=None):
        """Save payment screenshot"""
        payment = self.get_object()
        file_id = request.data.get("file_id")
        
        if not file_id:
            return Response(
                {"error": "No file_id provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has permission
        telegram_id = request.query_params.get('telegram_id')
        if not request.user.is_staff and str(payment.student.telegram_id) != telegram_id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        payment.screenshot_file_id = file_id
        payment.save()
        return Response({"status": "screenshot saved"})