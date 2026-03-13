from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Questionnaire, Question, Submission, Answer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'question_type', 'order', 'is_required', 'options')
    ordering = ('order',)

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_model', 'question_count', 'is_active', 'created_at')
    list_filter = ('target_model', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'created_by')
    inlines = [QuestionInline]
    fieldsets = (
        (_("Basic Information"), {
            'fields': ('title', 'description', 'target_model', 'is_active')
        }),
        (_("Metadata"), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = _("Number of Questions")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'text', 'question_type', 'order', 'is_required')
    list_filter = ('questionnaire', 'question_type', 'is_required')
    search_fields = ('text',)
    ordering = ('questionnaire', 'order')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'submitted_by', 'target_summary', 'submitted_at')
    list_filter = ('questionnaire', 'submitted_at', 'submitted_by')
    search_fields = ('questionnaire__title',)
    readonly_fields = ('questionnaire', 'submitted_by', 'submitted_at', 'content_type', 'object_id')

    def target_summary(self, obj):
        return f"{obj.content_type.name}: {obj.content_object}"
    target_summary.short_description = _("Target")

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('submission', 'question', 'answer_summary')
    list_filter = ('submission__questionnaire', 'question')
    search_fields = ('question__text', 'submission__questionnaire__title')

    def answer_summary(self, obj):
        if obj.value_text:
            return obj.value_text[:50]
        elif obj.value_number:
            return str(obj.value_number)
        elif obj.value_boolean is not None:
            return _("Yes") if obj.value_boolean else _("No")
        elif obj.value_date:
            return str(obj.value_date)
        return "---"
    answer_summary.short_description = _("Answer")
