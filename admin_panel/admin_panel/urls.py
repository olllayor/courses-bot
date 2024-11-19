from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mentors.views import MentorViewSet, MentorAvailabilityViewSet
from courses.views import CourseViewSet, LessonViewSet, QuizViewSet
from accounts.views import StudentViewSet
from progress.views import StudentProgressViewSet

router = DefaultRouter()
router.register(r'mentors', MentorViewSet)
router.register(r'mentor-availability', MentorAvailabilityViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'students', StudentViewSet)
router.register(r'progress', StudentProgressViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]