# payments/views.py
import logging

from accounts.models import Student
from django.utils import timezone
from payment.models import Payment
from payment.serializers import PaymentSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]  # Allow all access, we'll verify by telegram_id
    
    def get_queryset(self):
        """Filter payments based on user role and parameters"""
        queryset = Payment.objects.all()
        
        # Get admin status from telegram_id
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            from django.conf import settings
            admin_ids = getattr(settings, 'ADMIN_IDS', '').split(',')
            if telegram_id in admin_ids:
                logger.info(f"Admin {telegram_id} accessing all payments")
                return queryset
        
        # For non-admins, filter by student telegram_id
        if telegram_id:
            try:
                student = Student.objects.get(telegram_id=telegram_id)
                logger.info(f"User {telegram_id} accessing their payments")
                
                # Apply additional filters
                course_id = self.request.query_params.get('course')
                status_filter = self.request.query_params.get('status')
                
                filtered_queryset = queryset.filter(student=student)
                
                if course_id:
                    filtered_queryset = filtered_queryset.filter(course_id=course_id)
                    
                if status_filter:
                    filtered_queryset = filtered_queryset.filter(status=status_filter)
                    
                return filtered_queryset
            except Student.DoesNotExist:
                logger.warning(f"Student with telegram_id {telegram_id} not found")
                return Payment.objects.none()
        
        # Default to empty queryset if no telegram_id
        logger.warning("No telegram_id provided for payment listing")
        return Payment.objects.none()

    def create(self, request, *args, **kwargs):
        """Create payment with proper student association"""
        try:
            # Get student by telegram_id
            telegram_id = request.data.get('student')
            if not telegram_id:
                telegram_id = request.query_params.get('telegram_id')
            
            if not telegram_id:
                logger.error("No telegram_id provided for payment creation")
                return Response(
                    {'error': 'telegram_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                student = Student.objects.get(telegram_id=telegram_id)
            except Student.DoesNotExist:
                logger.error(f"Student with telegram_id {telegram_id} not found")
                # Try to create a new student if name is provided
                name = request.data.get('name')
                if name:
                    student = Student.objects.create(
                        telegram_id=telegram_id,
                        name=name
                    )
                    logger.info(f"Created new student {telegram_id} for payment")
                else:
                    return Response(
                        {'error': 'Student not found and no name provided to create one'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create payment data
            payment_data = {
                'student': student.id,
                'course': request.data.get('course'),
                'amount': request.data.get('amount'),
                'status': Payment.PENDING
            }
            
            serializer = self.get_serializer(data=payment_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
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

        # Check if user has permission using telegram_id
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            logger.error("No telegram_id provided for screenshot upload")
            return Response(
                {"error": "telegram_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if admin or payment owner
        from django.conf import settings
        admin_ids = getattr(settings, 'ADMIN_IDS', '').split(',')
        
        if telegram_id in admin_ids:
            is_admin = True
        else:
            is_admin = False
            
        if not is_admin and str(payment.student.telegram_id) != telegram_id:
            logger.warning(f"Unauthorized screenshot upload attempt by {telegram_id}")
            return Response(
                {"error": "You don't have permission to upload screenshot for this payment"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        payment.screenshot_file_id = file_id
        payment.save()
        logger.info(f"Screenshot saved for payment {payment.id} by {telegram_id}")
        return Response({"status": "screenshot saved"})
        
    @action(detail=True, methods=["POST"])
    def confirm(self, request, pk=None):
        """Confirm a pending payment"""
        payment = self.get_object()
        
        # Check admin permission via telegram_id
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            logger.error("No telegram_id provided for payment confirmation")
            return Response(
                {"error": "telegram_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify admin status
        from django.conf import settings
        admin_ids = getattr(settings, 'ADMIN_IDS', '').split(',')
        
        if telegram_id not in admin_ids:
            logger.warning(f"Unauthorized payment confirmation attempt by {telegram_id}")
            return Response(
                {"error": "Only administrators can confirm payments"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if payment.status != Payment.PENDING:
            logger.warning(f"Attempt to confirm non-pending payment {payment.id}")
            return Response(
                {"error": "Only pending payments can be confirmed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if screenshot was uploaded
        if not payment.screenshot_file_id:
            logger.warning(f"Attempt to confirm payment {payment.id} without screenshot")
            return Response(
                {"error": "Payment cannot be confirmed without a screenshot"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Confirm the payment
        payment.status = Payment.CONFIRMED
        payment.confirmed_at = timezone.now()
        payment.save()
        
        logger.info(f"Payment {payment.id} confirmed by admin {telegram_id}")
        
        # Return the updated payment
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
        
    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        """Cancel a pending payment"""
        payment = self.get_object()
        
        # Check admin permission via telegram_id
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            logger.error("No telegram_id provided for payment cancellation")
            return Response(
                {"error": "telegram_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify admin status
        from django.conf import settings
        admin_ids = getattr(settings, 'ADMIN_IDS', '').split(',')
        
        if telegram_id not in admin_ids:
            logger.warning(f"Unauthorized payment cancellation attempt by {telegram_id}")
            return Response(
                {"error": "Only administrators can cancel payments"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if payment.status != Payment.PENDING:
            logger.warning(f"Attempt to cancel non-pending payment {payment.id}")
            return Response(
                {"error": "Only pending payments can be cancelled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cancel the payment
        payment.status = Payment.CANCELLED
        payment.save()
        
        logger.info(f"Payment {payment.id} cancelled by admin {telegram_id}")
        
        # Return the updated payment
        serializer = self.get_serializer(payment)
        return Response(serializer.data)