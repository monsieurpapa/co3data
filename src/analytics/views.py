from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from cooperatives.models import Cooperative, Member, ProductionRecord
from questionnaires.models import Submission
from .services import KPIService
from .models import DataQualityAlert

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Filter by region if not superuser
        cooperatives = Cooperative.objects.all()
        members = Member.objects.all()
        production = ProductionRecord.objects.all()
        alerts = DataQualityAlert.objects.all()
        submissions = Submission.objects.all()
        
        if not user.is_superuser:
            if not user.region:
                cooperatives = cooperatives.none()
                members = members.none()
                production = production.none()
                alerts = alerts.none()
                submissions = submissions.none()
            else:
                cooperatives = cooperatives.filter(region=user.region)
                members = members.filter(cooperative__region=user.region)
                production = production.filter(farm__member__cooperative__region=user.region)
                alerts = alerts.filter(cooperative__region=user.region)
                submissions = submissions.filter(submitted_by__region=user.region)

        context['total_cooperatives'] = cooperatives.count()
        context['total_members'] = members.count()
        context['total_submissions'] = submissions.count()
        
        # Youth participation
        youth_counts = []
        annotated_youth = KPIService.get_cooperatives_with_youth_data(cooperatives)
        for coop in annotated_youth:
            pct = (coop.youth_members_count / coop.total_members_count * 100) if coop.total_members_count > 0 else 0
            youth_counts.append({
                'coop_name': coop.name,
                'youth_participation': round(pct, 2)
            })
            
        # Yield Calculation
        total_yield = 0
        coops_with_yield = 0
        annotated_yield = KPIService.get_cooperatives_with_yield_data(cooperatives)
        
        for coop in annotated_yield:
            if coop.total_farm_size_ha and coop.total_farm_size_ha > 0:
                prod = coop.total_production_kg or 0
                coop_yield = float(prod) / float(coop.total_farm_size_ha)
                
                if coop_yield > 0:
                    total_yield += coop_yield
                    coops_with_yield += 1
                  
        context['youth_counts'] = youth_counts
        context['avg_yield'] = round(total_yield / coops_with_yield, 2) if coops_with_yield > 0 else 0
        
        # Recent production
        context['recent_production'] = production.filter(
            record_type=ProductionRecord.RECORD_TYPE_GENERIC
        ).select_related('farm__member__cooperative').order_by('-harvest_date')[:10]
        
        # Recent deliveries
        context['recent_deliveries'] = production.filter(
            record_type=ProductionRecord.RECORD_TYPE_CHERRY
        ).select_related('member', 'station').order_by('-id')[:10]
        
        # Data Quality Alerts
        context['quality_alerts'] = alerts.select_related('cooperative', 'rule').filter(is_resolved=False).order_by('-alert_date')[:5]
        
        # Recent Submissions
        context['recent_submissions'] = submissions.select_related('questionnaire', 'submitted_by').order_by('-submitted_at')[:5]
        
        return context
