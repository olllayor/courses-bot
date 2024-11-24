# mentors/admin.py
from django.contrib import admin
from .models import Mentor, MentorAvailability

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ['name', 'bio']
    search_fields = ['name']

@admin.register(MentorAvailability)
class MentorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'start_time', 'end_time', 'is_available']
    list_filter = ['mentor', 'is_available', 'start_time']
