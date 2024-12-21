# courses/admin.py
from django.contrib import admin
from .models import Course, Lesson, Quiz
from django.utils.html import format_html


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "mentor", "price", "created_at"]
    list_filter = ["mentor", "created_at"]
    search_fields = ["title", "description"]


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "is_free", "created_at", "video_status"]
    list_filter = ["course", "is_free", "created_at"]
    search_fields = ["title", "content"]
    readonly_fields = ("created_at", "updated_at")
    inlines = [QuizInline]

    fieldsets = (
        ("Basic Information", {"fields": ("course", "title", "is_free")}),
        ("Content", {"fields": ("content",)}),
        (
            "Video Information",
            {
                "fields": ("telegram_video_id",),
                "description": "Enter the video ID provided by Telegram",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def video_status(self, obj):
        if obj.telegram_video_id:
            return format_html('<span style="color: green;">✓</span> Video Added')
        return format_html('<span style="color: red;">×</span> No Video')

    video_status.short_description = "Video Status"

    def save_model(self, request, obj, form, change):
        # You can add any video ID validation here if needed
        super().save_model(request, obj, form, change)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["lesson", "id"]
    list_filter = ["lesson__course"]
