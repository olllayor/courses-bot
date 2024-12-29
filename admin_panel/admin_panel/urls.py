from accounts.views import StudentViewSet
from courses.views import CourseViewSet, LessonViewSet, QuizViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from mentors.views import MentorAvailabilityViewSet, MentorViewSet
from payment.views import PaymentViewSet
from webinar.views import WebinarViewSet
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

# Schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Courses Bot API",
        default_version="v1",
        description="API documentation for Courses Bot",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Router configuration
router = DefaultRouter()
router.register(r"students", StudentViewSet)
router.register(r"mentors", MentorViewSet)
router.register(r"webinars", WebinarViewSet)
router.register(r"mentor-availability", MentorAvailabilityViewSet)
router.register(r"courses", CourseViewSet)
router.register(r"lessons", LessonViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"quizzes", QuizViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    # API documentation URLs
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # path('api/api.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
