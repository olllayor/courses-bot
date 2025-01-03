# accounts/admin.py
from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'telegram_id', 'created_at']
    search_fields = ['name', 'phone_number', 'telegram_id']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'auth_token', 'token_created_at']