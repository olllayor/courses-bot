# payments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from accounts.models import Student
from payment.models import Payment
from payment.serializers import PaymentSerializer
from courses.models import Course
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework import serializers
from hashlib import sha256


class HasValidToken(BasePermission):
    """
    Custom permission to check if a student has a valid token.
    """

    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            return False

        token = auth_header[6:]  # Extract the token

        try:
            hashed_token = sha256(token.encode()).hexdigest()  # Hash the received token
            student = Student.objects.get(auth_token=hashed_token)
            return student.is_token_valid()
        except Student.DoesNotExist:
            return False


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [HasValidToken]

    def get_permissions(self):
        if self.action in ["create", "save_screenshot"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter payments based on user role and parameters"""
        queryset = Payment.objects.all()

        if self.request.user.is_staff:
            return queryset

        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            return Payment.objects.none()

        token = auth_header[6:]  # Extract the token

        try:
            hashed_token = sha256(token.encode()).hexdigest()
            student = Student.objects.get(auth_token=hashed_token)
            return queryset.filter(student=student)
        except Student.DoesNotExist:
            return Payment.objects.none()

    def create(self, request, *args, **kwargs):
        """Create payment with proper student association"""
        try:
            # Get student by auth token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Token "):
                raise APIException(detail="Authorization header is required")

            token = auth_header[6:]  # Extract the token
            hashed_token = sha256(token.encode()).hexdigest()
            student = Student.objects.get(auth_token=hashed_token)

            # Get course
            course_id = request.data.get("course")
            if not course_id:
                raise APIException(detail="Course id is required")

            course = Course.objects.get(id=course_id)

            # Validate payment amount
            amount = request.data.get("amount")
            if not amount:
                raise APIException(detail="Amount is required")

            if float(amount) != float(course.price):
                raise APIException(detail="Payment amount must match course price")

            # Check if the student has already purchased the course
            if Payment.objects.filter(
                student=student, course=course, status=Payment.CONFIRMED
            ).exists():
                raise APIException(detail="Course already purchased")

            # Create payment data
            payment_data = {
                "student": student.id,
                "course": course.id,
                "amount": amount,
                "status": Payment.PENDING,
            }

            serializer = self.get_serializer(data=payment_data)
            serializer.is_valid(raise_for_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["PUT"])
    def save_screenshot(self, request, pk=None):
        """Save payment screenshot"""
        payment = self.get_object()
        file_id = request.data.get("file_id")

        if not file_id:
            return Response(
                {"error": "No file_id provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has permission
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            return Response(status=status.HTTP_403_FORBIDDEN)

        token = auth_header[6:]  # Extract the token
        try:
            hashed_token = sha256(token.encode()).hexdigest()
            student = Student.objects.get(auth_token=hashed_token)
            if str(payment.student.id) != str(student.id):
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Student.DoesNotExist:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if payment.status != Payment.PENDING:
            return Response(
                {"error": "Payment already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.screenshot_file_id = file_id
        payment.save()
        return Response({"status": "screenshot saved"})

    @action(detail=True, methods=["POST"])
    def confirm(self, request, pk=None):
        """Confirm payment by admin"""
        payment = self.get_object()
        if payment.confirm_payment():
            serializer = self.get_serializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Can not confirm this payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        """Cancel payment by admin"""
        payment = self.get_object()
        if payment.cancel_payment():
            serializer = self.get_serializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Can not cancel this payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
