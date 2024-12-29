from django.contrib import admin
from .models import Webinar  # Fix the import

@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ["title", "mentor", "created_at"]
    list_filter = ["mentor", "created_at"]
    search_fields = ["title", "mentor__name"]  # Added search by mentor name
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Basic Information", {"fields": ("mentor", "title")}),
        (
            "Video Information",
            {
                "fields": ("video_telegram_id",),
                "description": "Enter the video ID provided by Telegram",
            },
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )