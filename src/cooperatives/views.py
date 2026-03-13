from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from core.mixins import RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin
from .models import (
    Cooperative,
    Member,
    ProductionRecord,
    FinancialRecord,
    Buyer,
    CooperativeCertificate,
    CooperativeSale,
)
from .forms import (
    MemberForm,
    CooperativeForm,
    CherryDeliveryForm,
    ProductionRecordForm,
    FinancialRecordForm,
    BuyerForm,
    CooperativeCertificateForm,
    CooperativeSaleForm,
)

from questionnaires.models import Questionnaire, Submission

class CooperativeListView(RegionalAccessMixin, ListView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_list.html'
    context_object_name = 'cooperatives'

from django.core.paginator import Paginator

class CooperativeDetailView(RegionalAccessMixin, DetailView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_detail.html'
    context_object_name = 'cooperative'
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Paginate members
        members_list = self.object.members.all().order_by('last_name', 'first_name')
        paginator = Paginator(members_list, 20) # 20 members per page
        page_number = self.request.GET.get('page')
        context['members'] = paginator.get_page(page_number)
        
        # Add active questionnaires for cooperatives
        context['available_questionnaires'] = Questionnaire.objects.filter(target_model='cooperative', is_active=True)

        # Certificates + sales history
        context['certificates'] = self.object.certificates.all().order_by('-issued_date')
        context['sales'] = self.object.sales.select_related('buyer').order_by('-year', '-quantity_kg')

        # Analytics data for charts
        context['sales_by_year'] = (
            self.object.sales.values('year')
            .annotate(total_qty=Sum('quantity_kg'))
            .order_by('year')
        )
        context['sales_by_destination'] = (
            self.object.sales.values('destination_country')
            .annotate(total_qty=Sum('quantity_kg'))
            .order_by('-total_qty')
        )

        # Buyer list for sale form
        context['buyers'] = Buyer.objects.all().order_by('name')
        return context

class CooperativeCreateView(RoleRequiredMixin, CreateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = 'cooperatives/cooperative_form.html'
    required_roles = ['admin', 'regional_officer']

    def form_valid(self, form):
        # Ensure cooperatives are tied to a region (required by the model)
        if not hasattr(self.request.user, 'region') or self.request.user.region is None:
            form.add_error(None, _('Unable to create a cooperative because your user account is not assigned to a region.'))
            return self.form_invalid(form)

        form.instance.region = self.request.user.region
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.object.unique_id})

class CooperativeUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = 'cooperatives/cooperative_form.html'
    success_url = reverse_lazy('cooperatives:cooperative_list')
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class CooperativeDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = Cooperative
    template_name = 'cooperatives/cooperative_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:cooperative_list')
    required_roles = ['admin']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class MemberListView(RegionalAccessMixin, ListView):
    model = Member
    template_name = 'cooperatives/member_list.html'
    context_object_name = 'members'

class MemberDetailView(RegionalAccessMixin, DetailView):
    model = Member
    template_name = 'cooperatives/member_detail.html'
    context_object_name = 'member'
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

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
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class MemberDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = Member
    template_name = 'cooperatives/member_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:member_list')
    required_roles = ['manager', 'admin']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'


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
    required_roles = ["manager", "admin", "regional_officer", "agronomist", "supervisor", "station_chef"]

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
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class CherryDeliveryUpdateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, UpdateView):
    model = ProductionRecord
    form_class = CherryDeliveryForm
    template_name = "cooperatives/cherry_delivery_form.html"
    success_url = reverse_lazy("cooperatives:cherry_delivery_list")
    required_roles = ["manager", "admin", "regional_officer", "agronomist", "supervisor", "station_chef"]
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        cooperative = None
        if hasattr(self.request.user, "region"):
            cooperative = Cooperative.objects.filter(region=self.request.user.region).first()
        if cooperative:
            kwargs["cooperative"] = cooperative
        return kwargs


class CherryDeliveryDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = ProductionRecord
    template_name = "cooperatives/cherry_delivery_confirm_delete.html"
    success_url = reverse_lazy("cooperatives:cherry_delivery_list")
    required_roles = ["admin", "manager", "supervisor"]
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'


# ============================================================================
# PRODUCTION RECORD VIEWS (Generic - Coffee/Cocoa)
# ============================================================================

class ProductionRecordListView(RegionalAccessMixin, ListView):
    model = ProductionRecord
    template_name = 'cooperatives/production_record_list.html'
    context_object_name = 'production_records'
    paginate_by = 20
    
    def get_queryset(self):
        return ProductionRecord.objects.filter(
            record_type=ProductionRecord.RECORD_TYPE_GENERIC
        ).select_related('farm__member__cooperative').order_by('-harvest_date')

class ProductionRecordDetailView(RegionalAccessMixin, DetailView):
    model = ProductionRecord
    template_name = 'cooperatives/production_record_detail.html'
    context_object_name = 'production_record'
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get questionnaire submissions for this production record
        content_type = ContentType.objects.get_for_model(ProductionRecord)
        context['submissions'] = Submission.objects.filter(
            content_type=content_type,
            object_id=self.object.pk
        ).select_related('questionnaire').order_by('-submitted_at')
        return context

class ProductionRecordCreateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, CreateView):
    model = ProductionRecord
    form_class = ProductionRecordForm
    template_name = 'cooperatives/production_record_form.html'
    success_url = reverse_lazy('cooperatives:production_record_list')
    required_roles = ['admin', 'manager', 'agronomist', 'supervisor']

class ProductionRecordUpdateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, UpdateView):
    model = ProductionRecord
    form_class = ProductionRecordForm
    template_name = 'cooperatives/production_record_form.html'
    success_url = reverse_lazy('cooperatives:production_record_list')
    required_roles = ['admin', 'manager', 'agronomist']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class ProductionRecordDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = ProductionRecord
    template_name = 'cooperatives/production_record_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:production_record_list')
    required_roles = ['admin', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'


# ============================================================================
# FINANCIAL RECORD VIEWS
# ============================================================================

class FinancialRecordListView(RegionalAccessMixin, ListView):
    model = FinancialRecord
    template_name = 'cooperatives/financial_record_list.html'
    context_object_name = 'financial_records'
    paginate_by = 20
    
    def get_queryset(self):
        return FinancialRecord.objects.select_related('cooperative').order_by('-transaction_date')

class FinancialRecordDetailView(RegionalAccessMixin, DetailView):
    model = FinancialRecord
    template_name = 'cooperatives/financial_record_detail.html'
    context_object_name = 'financial_record'
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get questionnaire submissions for this financial record
        content_type = ContentType.objects.get_for_model(FinancialRecord)
        context['submissions'] = Submission.objects.filter(
            content_type=content_type,
            object_id=self.object.pk
        ).select_related('questionnaire').order_by('-submitted_at')
        return context

class FinancialRecordCreateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, CreateView):
    model = FinancialRecord
    form_class = FinancialRecordForm
    template_name = 'cooperatives/financial_record_form.html'
    success_url = reverse_lazy('cooperatives:financial_record_list')
    required_roles = ['admin', 'manager']

class FinancialRecordUpdateView(RegionalAccessMixin, RoleRequiredMixin, RegionalFormMixin, UpdateView):
    model = FinancialRecord
    form_class = FinancialRecordForm
    template_name = 'cooperatives/financial_record_form.html'
    success_url = reverse_lazy('cooperatives:financial_record_list')
    required_roles = ['admin', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'

class FinancialRecordDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = FinancialRecord
    template_name = 'cooperatives/financial_record_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:financial_record_list')
    required_roles = ['admin']


# =============================================================================
# BUYERS
# =============================================================================

class BuyerListView(RegionalAccessMixin, ListView):
    model = Buyer
    template_name = 'cooperatives/buyer_list.html'
    context_object_name = 'buyers'
    paginate_by = 20

    def get_queryset(self):
        return Buyer.objects.order_by('name')


class BuyerCreateView(RegionalAccessMixin, RoleRequiredMixin, CreateView):
    model = Buyer
    form_class = BuyerForm
    template_name = 'cooperatives/buyer_form.html'
    success_url = reverse_lazy('cooperatives:buyer_list')
    required_roles = ['admin', 'regional_officer', 'manager']


class BuyerUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = Buyer
    form_class = BuyerForm
    template_name = 'cooperatives/buyer_form.html'
    success_url = reverse_lazy('cooperatives:buyer_list')
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'


class BuyerDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = Buyer
    template_name = 'cooperatives/buyer_confirm_delete.html'
    success_url = reverse_lazy('cooperatives:buyer_list')
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'


# =============================================================================
# COOPERATIVE CERTIFICATES
# =============================================================================

class CooperativeCertificateListView(RegionalAccessMixin, ListView):
    model = CooperativeCertificate
    template_name = 'cooperatives/cooperative_certificate_list.html'
    context_object_name = 'certificates'
    paginate_by = 20

    def get_cooperative(self):
        return get_object_or_404(Cooperative, unique_id=self.kwargs.get('uuid'))

    def get_queryset(self):
        return CooperativeCertificate.objects.filter(cooperative=self.get_cooperative()).order_by('-issued_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.get_cooperative()
        return context


class CooperativeCertificateCreateView(RegionalAccessMixin, RoleRequiredMixin, CreateView):
    model = CooperativeCertificate
    form_class = CooperativeCertificateForm
    template_name = 'cooperatives/cooperative_certificate_form.html'
    required_roles = ['admin', 'regional_officer', 'manager']

    def dispatch(self, request, *args, **kwargs):
        self.cooperative = get_object_or_404(Cooperative, unique_id=kwargs.get('uuid'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.cooperative = self.cooperative
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.cooperative.unique_id})


class CooperativeCertificateUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = CooperativeCertificate
    form_class = CooperativeCertificateForm
    template_name = 'cooperatives/cooperative_certificate_form.html'
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'cert_uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.object.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.object.cooperative.unique_id})


class CooperativeCertificateDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = CooperativeCertificate
    template_name = 'cooperatives/cooperative_certificate_confirm_delete.html'
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'cert_uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.object.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.object.cooperative.unique_id})


# =============================================================================
# COOPERATIVE SALES
# =============================================================================

class CooperativeSaleListView(RegionalAccessMixin, ListView):
    model = CooperativeSale
    template_name = 'cooperatives/cooperative_sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_cooperative(self):
        return get_object_or_404(Cooperative, unique_id=self.kwargs.get('uuid'))

    def get_queryset(self):
        return CooperativeSale.objects.filter(cooperative=self.get_cooperative()).select_related('buyer').order_by('-year', '-quantity_kg')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.get_cooperative()
        return context


class CooperativeSaleCreateView(RegionalAccessMixin, RoleRequiredMixin, CreateView):
    model = CooperativeSale
    form_class = CooperativeSaleForm
    template_name = 'cooperatives/cooperative_sale_form.html'
    required_roles = ['admin', 'regional_officer', 'manager']

    def dispatch(self, request, *args, **kwargs):
        self.cooperative = get_object_or_404(Cooperative, unique_id=kwargs.get('uuid'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.cooperative = self.cooperative
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.cooperative.unique_id})


class CooperativeSaleUpdateView(RegionalAccessMixin, RoleRequiredMixin, UpdateView):
    model = CooperativeSale
    form_class = CooperativeSaleForm
    template_name = 'cooperatives/cooperative_sale_form.html'
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'sale_uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.object.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.object.cooperative.unique_id})


class CooperativeSaleDeleteView(RegionalAccessMixin, RoleRequiredMixin, DeleteView):
    model = CooperativeSale
    template_name = 'cooperatives/cooperative_sale_confirm_delete.html'
    required_roles = ['admin', 'regional_officer', 'manager']
    slug_field = 'unique_id'
    slug_url_kwarg = 'sale_uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cooperative'] = self.object.cooperative
        return context

    def get_success_url(self):
        return reverse_lazy('cooperatives:cooperative_detail', kwargs={'uuid': self.object.cooperative.unique_id})
