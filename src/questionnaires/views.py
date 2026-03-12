from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django.contrib.contenttypes.models import ContentType
from core.mixins import RoleRequiredMixin, RegionalAccessMixin
from .models import Questionnaire, Submission, Answer
from .forms import QuestionnaireSubmissionForm
from cooperatives.models import Cooperative, Member

class QuestionnaireListView(RoleRequiredMixin, ListView):
    model = Questionnaire
    template_name = 'questionnaires/questionnaire_list.html'
    context_object_name = 'questionnaires'
    required_roles = ['member', 'manager', 'regional_officer', 'apex_body', 'government', 'admin']

class QuestionnaireDetailView(RoleRequiredMixin, DetailView):
    model = Questionnaire
    template_name = 'questionnaires/questionnaire_detail.html'
    context_object_name = 'questionnaire'
    required_roles = ['member', 'manager', 'regional_officer', 'apex_body', 'government', 'admin']

class QuestionnaireSubmissionView(RoleRequiredMixin, FormView):
    template_name = 'questionnaires/submission_form.html'
    form_class = QuestionnaireSubmissionForm
    required_roles = ['member', 'manager', 'regional_officer', 'admin'] # Enumerators usually have 'member' or specific roles

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['questionnaire'] = get_object_or_404(Questionnaire, pk=self.kwargs['pk'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questionnaire'] = get_object_or_404(Questionnaire, pk=self.kwargs['pk'])
        
        # Determine target object
        target_id = self.request.GET.get('target_id')
        if context['questionnaire'].target_model == 'cooperative':
            context['target_object'] = get_object_or_404(Cooperative, pk=target_id) if target_id else None
        else:
            context['target_object'] = get_object_or_404(Member, pk=target_id) if target_id else None
            
        return context

    def form_valid(self, form):
        questionnaire = get_object_or_404(Questionnaire, pk=self.kwargs['pk'])
        target_id = self.request.GET.get('target_id')
        
        if questionnaire.target_model == 'cooperative':
            target_obj = get_object_or_404(Cooperative, pk=target_id)
        else:
            target_obj = get_object_or_404(Member, pk=target_id)

        submission = Submission.objects.create(
            questionnaire=questionnaire,
            submitted_by=self.request.user,
            content_type=ContentType.objects.get_for_model(target_obj),
            object_id=target_obj.pk
        )
        form.save(submission)
        
        # Trigger validation
        from analytics.services import ValidationService
        ValidationService.validate_submission(submission)
        
        return redirect('questionnaires:submission_list')

class SubmissionListView(RegionalAccessMixin, RoleRequiredMixin, ListView):
    model = Submission
    template_name = 'questionnaires/submission_list.html'
    context_object_name = 'submissions'
    required_roles = ['manager', 'regional_officer', 'admin']

    def get_queryset(self):
        qs = super().get_queryset()
        # Additional regional filtering if not already handled by RegionalAccessMixin
        # Submission connects to target via GFK, so we need to filter based on target's region
        user = self.request.user
        if not user.is_superuser and user.region:
            # This is tricky with GFK, but for now we filter by submitted_by.region or similar
            # If target is Cooperative/Member, we check their region
            return qs.filter(submitted_by__region=user.region)
        return qs

class SubmissionDetailView(RegionalAccessMixin, RoleRequiredMixin, DetailView):
    model = Submission
    template_name = 'questionnaires/submission_detail.html'
    context_object_name = 'submission'
    required_roles = ['manager', 'regional_officer', 'admin']
