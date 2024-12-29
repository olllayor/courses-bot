# accounts/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Student
from .serializers import StudentSerializer
from hashlib import sha256


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def refresh_token(self, request):
        """Refresh authentication token for a student"""
        telegram_id = request.data.get("telegram_id")

        if not telegram_id:
            return Response(
                {"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(telegram_id=telegram_id)

            # Generate new token
            token = student.refresh_token()

            return Response(
                {"token": token, "student_id": student.id, "name": student.name}
            )
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def authenticate(self, request):
        telegram_id = request.data.get("telegram_id")
        name = request.data.get("name")

        if not telegram_id or not name:
            return Response(
                {"error": "Both telegram_id and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student, created = Student.objects.get_or_create(
                telegram_id=telegram_id, defaults={"name": name}
            )

            # Generate new token on every authentication
            token = student.generate_token()

            return Response(
                {
                    "student_id": student.id,
                    "name": student.name,
                    "telegram_id": student.telegram_id,
                    "token": token,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
