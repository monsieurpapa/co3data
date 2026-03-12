from django.contrib import admin
from .models import Questionnaire, Question, Submission, Answer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_model', 'created_at', 'is_active')
    inlines = [QuestionInline]

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'submitted_by', 'submitted_at', 'content_object')
    list_filter = ('questionnaire', 'submitted_at')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('submission', 'question', 'value_text', 'value_number', 'value_boolean')
