# mentors/admin.py
from django.contrib import admin
from .models import Mentor, MentorAvailability

class MentorAvailabilityInline(admin.TabularInline):
    model = MentorAvailability
    extra = 1
    readonly_fields = ('is_available',)

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('name', 'availability_count')
    search_fields = ('name',)
    inlines = [MentorAvailabilityInline]

    def availability_count(self, obj):
        return obj.availability.count()
    availability_count.short_description = 'Availability Count'

@admin.register(MentorAvailability)
class MentorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'start_time', 'end_time', 'is_available')
    list_filter = ('mentor', 'is_available')
    search_fields = ('mentor__name',)
    date_hierarchy = 'start_time'
