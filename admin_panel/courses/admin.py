# courses/admin.py
from django.contrib import admin
from .models import Course, Lesson, Quiz

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentor')
    list_filter = ('mentor',)
    search_fields = ('title', 'mentor__name')

class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 1

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'is_free')
    list_filter = ('course', 'is_free')
    search_fields = ('title', 'course__title')
    inlines = [QuizInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'get_question_count')
    list_filter = ('lesson__course',)
    search_fields = ('lesson__title',)

    def get_question_count(self, obj):
        return len(obj.questions)
    get_question_count.short_description = 'Number of Questions'