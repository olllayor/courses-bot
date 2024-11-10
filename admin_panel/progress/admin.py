
from django.contrib import admin
from .models import StudentProgress

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'quiz_score', 'completed_at')
    list_filter = ('student', 'lesson__course', 'completed_at')
    search_fields = ('student__name', 'lesson__title')
    date_hierarchy = 'completed_at'