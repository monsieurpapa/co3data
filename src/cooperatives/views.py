from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from core.mixins import RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin
from .models import Cooperative, Member
from .forms import MemberForm, CooperativeForm

from questionnaires.models import Questionnaire

class CooperativeListView(RegionalAccessMixin, ListView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_list.html'
    context_object_name = 'cooperatives'

class CooperativeDetailView(RegionalAccessMixin, DetailView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_detail.html'
    context_object_name = 'cooperative'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.all()
        # Add active questionnaires for cooperatives
        context['available_questionnaires'] = Questionnaire.objects.filter(target_model='cooperative', is_active=True)
        return context

class CooperativeCreateView(RoleRequiredMixin, CreateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = 'cooperatives/cooperative_form.html'
    success_url = reverse_lazy('cooperatives:cooperative_list')
    required_roles = ['admin', 'regional_officer']

class CooperativeUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = 'cooperatives/cooperative_form.html'
    success_url = reverse_lazy('cooperatives:cooperative_list')
    required_roles = ['admin', 'regional_officer', 'manager']

class CooperativeDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:cooperative_list')
    required_roles = ['admin']

class MemberListView(RegionalAccessMixin, ListView):
    model = Member
    template_name = 'cooperatives/member_list.html'
    context_object_name = 'members'

class MemberDetailView(RegionalAccessMixin, DetailView):
    model = Member
    template_name = 'cooperatives/member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Link back to cooperative for breadcrumbs
        context['cooperative'] = self.object.cooperative
        context['farms'] = self.object.farms.all()
        # Get production records for all farms of this member
        from .models import ProductionRecord
        context['production_records'] = ProductionRecord.objects.filter(farm__member=self.object)
        # Add active questionnaires for members
        context['available_questionnaires'] = Questionnaire.objects.filter(target_model='member', is_active=True)
        return context

class MemberCreateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'cooperatives/member_form.html'
    success_url = reverse_lazy('cooperatives:member_list')
    required_roles = ['manager', 'admin', 'regional_officer']

class MemberUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'cooperatives/member_form.html'
    success_url = reverse_lazy('cooperatives:member_list')
    required_roles = ['manager', 'admin', 'regional_officer']

class MemberDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = Member
    template_name = 'cooperatives/member_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:member_list')
    required_roles = ['manager', 'admin']
