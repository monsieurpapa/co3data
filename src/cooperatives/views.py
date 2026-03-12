from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from core.mixins import RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin
from .models import Cooperative, Member, ProductionRecord
from .forms import MemberForm, CooperativeForm, CherryDeliveryForm

from questionnaires.models import Questionnaire

class CooperativeListView(RegionalAccessMixin, ListView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_list.html'
    context_object_name = 'cooperatives'

from django.core.paginator import Paginator

class CooperativeDetailView(RegionalAccessMixin, DetailView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_detail.html'
    context_object_name = 'cooperative'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Paginate members
        members_list = self.object.members.all().order_by('last_name', 'first_name')
        paginator = Paginator(members_list, 20) # 20 members per page
        page_number = self.request.GET.get('page')
        context['members'] = paginator.get_page(page_number)
        
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
        context['cooperative'] = self.object.cooperative
        context['farms'] = self.object.farms.all()
        
        prod_list = ProductionRecord.objects.filter(farm__member=self.object).order_by('-harvest_date')
        paginator = Paginator(prod_list, 10) # 10 records per page
        page_number = self.request.GET.get('page')
        context['production_records'] = paginator.get_page(page_number)
        
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


class CherryDeliveryListView(RegionalAccessMixin, ListView):
    model = ProductionRecord
    template_name = "cooperatives/cherry_delivery_list.html"
    context_object_name = "deliveries"

    def get_queryset(self):
        qs = ProductionRecord.objects.filter(record_type=ProductionRecord.RECORD_TYPE_CHERRY).select_related(
            "station", "member"
        )

        station_id = self.request.GET.get("station")
        farmer_code = self.request.GET.get("farmer_code")
        sync_status = self.request.GET.get("sync_status")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if station_id:
            qs = qs.filter(station_id=station_id)
        if farmer_code:
            qs = qs.filter(member__farmer_code__icontains=farmer_code)
        if sync_status == "pending":
            qs = qs.filter(is_locally_created=True)
        elif sync_status == "synced":
            qs = qs.filter(is_locally_created=False)
        if date_from:
            qs = qs.filter(purchase_date__gte=date_from)
        if date_to:
            qs = qs.filter(purchase_date__lte=date_to)

        return qs.order_by("-purchase_date", "-id")

    def get_context_data(self, **kwargs):
        from .models import WashingStation

        context = super().get_context_data(**kwargs)
        context["stations"] = WashingStation.objects.filter(is_active=True)
        context["selected_station"] = self.request.GET.get("station") or ""
        return context


class CherryDeliveryCreateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, CreateView):
    model = ProductionRecord
    form_class = CherryDeliveryForm
    template_name = "cooperatives/cherry_delivery_form.html"
    success_url = reverse_lazy("cooperatives:cherry_delivery_list")
    required_roles = ["manager", "admin", "regional_officer"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        cooperative = None
        if hasattr(self.request.user, "region"):
            cooperative = Cooperative.objects.filter(region=self.request.user.region).first()
        if cooperative:
            kwargs["cooperative"] = cooperative
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            from django.forms.models import model_to_dict
            from sync.models import PendingChange

            device = getattr(self.request.user, "devices", None)
            device = device.first() if device is not None else None
            if device:
                PendingChange.objects.create(
                    device=device,
                    content_object=self.object,
                    change_type="create",
                    payload=model_to_dict(self.object),
                )
        except Exception:
            # Offline queuing is best-effort; failures here should not block main flow.
            pass
        return response


class CherryDeliveryDetailView(RegionalAccessMixin, DetailView):
    model = ProductionRecord
    template_name = "cooperatives/cherry_delivery_detail.html"
    context_object_name = "delivery"
