from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView, CreateView
from django.contrib.contenttypes.models import ContentType
from core.mixins import RoleRequiredMixin, RegionalAccessMixin
from .models import Questionnaire, Submission, Answer
from .forms import QuestionnaireSubmissionForm, QuestionFormSet
from cooperatives.models import Cooperative, Member
from users.models import User

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
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

    # Roles that are allowed to edit/add questions
    editable_roles = ['manager', 'regional_officer', 'admin']

    def user_can_edit_questions(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return getattr(user, 'role', None) in self.editable_roles

    def get_formset(self):
        return QuestionFormSet(queryset=self.get_object().questions.all(), prefix='questions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit_questions'] = self.user_can_edit_questions()
        if 'question_formset' not in context:
            context['question_formset'] = self.get_formset()

        # For cooperative-specific questionnaires, allow selecting which cooperatives it applies to
        from cooperatives.models import Cooperative
        context['all_cooperatives'] = Cooperative.objects.all().order_by('name')
        context['assigned_cooperatives'] = self.object.cooperatives.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.user_can_edit_questions():
            return redirect('questionnaires:questionnaire_detail', uuid=self.kwargs.get('uuid'))

        form_type = request.POST.get('form_type')

        if form_type == 'cooperatives':
            # Update assigned cooperatives only
            cooperative_ids = request.POST.getlist('cooperatives')
            from cooperatives.models import Cooperative
            if cooperative_ids:
                cooperatives = Cooperative.objects.filter(unique_id__in=cooperative_ids)
                self.object.cooperatives.set(cooperatives)
            else:
                self.object.cooperatives.clear()
            return redirect('questionnaires:questionnaire_detail', uuid=self.kwargs.get('uuid'))

        # Default: handle question formset
        formset = QuestionFormSet(request.POST, queryset=self.object.questions.all(), prefix='questions')
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.questionnaire = self.object
                instance.save()
            for instance in formset.deleted_objects:
                instance.delete()
            return redirect('questionnaires:questionnaire_detail', uuid=self.kwargs.get('uuid'))

        return self.render_to_response(self.get_context_data(question_formset=formset))


class QuestionnaireCreateView(RoleRequiredMixin, CreateView):
    model = Questionnaire
    fields = ['title', 'description', 'target_model', 'is_active']
    template_name = 'questionnaires/questionnaire_form.html'
    success_url = reverse_lazy('questionnaires:questionnaire_list')
    required_roles = ['admin', 'manager', 'regional_officer']

class QuestionnaireSubmissionView(RoleRequiredMixin, FormView):
    template_name = 'questionnaires/submission_form.html'
    form_class = QuestionnaireSubmissionForm
    required_roles = ['member', 'manager', 'regional_officer', 'admin']

    def get_target_object(self, questionnaire, target_id):
        """Get target object based on questionnaire target_model"""
        if target_id is None:
            return None
            
        try:
            if questionnaire.target_model == 'cooperative':
                return get_object_or_404(Cooperative, unique_id=target_id)
            elif questionnaire.target_model == 'member':
                return get_object_or_404(Member, unique_id=target_id)
            elif questionnaire.target_model == 'user':
                return get_object_or_404(User, unique_id=target_id)
            # elif questionnaire.target_model == 'financial_record':
            #     return get_object_or_404(FinancialRecord, unique_id=target_id)
            # elif questionnaire.target_model == 'production':
            #     return get_object_or_404(ProductionRecord, unique_id=target_id)
            pass
        except:
            return None
        return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['questionnaire'] = get_object_or_404(Questionnaire, unique_id=self.kwargs['uuid'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questionnaire = get_object_or_404(Questionnaire, unique_id=self.kwargs['uuid'])
        context['questionnaire'] = questionnaire
        
        target_id = self.request.GET.get('target_id')
        context['target_object'] = self.get_target_object(questionnaire, target_id)
        context['target_type'] = questionnaire.target_model
            
        return context

    def form_valid(self, form):
        questionnaire = get_object_or_404(Questionnaire, unique_id=self.kwargs['uuid'])
        target_id = self.request.GET.get('target_id')
        target_obj = self.get_target_object(questionnaire, target_id)
        
        if target_obj is None:
            return redirect('questionnaires:questionnaire_list')

        submission = Submission.objects.create(
            questionnaire=questionnaire,
            submitted_by=self.request.user,
            content_type=ContentType.objects.get_for_model(target_obj),
            object_id=target_obj.pk
        )
        form.save(submission)
        
        # Trigger validation if available
        try:
            from analytics.services import ValidationService
            ValidationService.validate_submission(submission)
        except:
            pass
        
        return redirect('questionnaires:submission_list')

class SubmissionListView(RegionalAccessMixin, RoleRequiredMixin, ListView):
    model = Submission
    template_name = 'questionnaires/submission_list.html'
    context_object_name = 'submissions'
    required_roles = ['manager', 'regional_officer', 'admin']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_superuser and user.region:
            return qs.filter(submitted_by__region=user.region)
        return qs

class SubmissionDetailView(RegionalAccessMixin, RoleRequiredMixin, DetailView):
    model = Submission
    template_name = 'questionnaires/submission_detail.html'
    context_object_name = 'submission'
    required_roles = ['manager', 'regional_officer', 'admin']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'
