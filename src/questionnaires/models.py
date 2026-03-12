from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Questionnaire(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    TARGET_MODEL_CHOICES = (
        ("cooperative", _("Cooperative")),
        ("member", _("Member")),
    )
    target_model = models.CharField(max_length=50, choices=TARGET_MODEL_CHOICES, default="cooperative")

    class Meta:
        verbose_name = _("Questionnaire")
        verbose_name_plural = _("Questionnaires")

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ("text", _("Text Input")),
        ("number", _("Number Input")),
        ("select", _("Select (Dropdown)")),
        ("multiselect", _("Multi-Select")),
        ("date", _("Date Input")),
        ("boolean", _("Yes/No")),
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["order"]

    def __str__(self):
        return self.text

class Submission(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Submission for {self.questionnaire.title} by {self.submitted_by or 'Anonymous'}"

class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        unique_together = ("submission", "question")

    def __str__(self):
        return f"Answer to {self.question.text}"
