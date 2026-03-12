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
        
        # Youth participation & Yield
        youth_counts = []
        total_yield = 0
        coops_with_yield = 0
        
        for coop in cooperatives:
            # Youth
            youth_participation = KPIService.calculate_youth_participation(coop)
            youth_counts.append({
                'coop_name': coop.name,
                'youth_participation': round(youth_participation, 2)
            })
            
            # Yield
            coop_yield = KPIService.calculate_yield_per_hectare(coop)
            if coop_yield > 0:
                total_yield += coop_yield
                coops_with_yield += 1
                  
        context['youth_counts'] = youth_counts
        context['avg_yield'] = round(total_yield / coops_with_yield, 2) if coops_with_yield > 0 else 0
        
        # Recent production
        context['recent_production'] = production.select_related('farm__member__cooperative').order_by('-harvest_date')[:10]
        
        # Data Quality Alerts
        context['quality_alerts'] = alerts.select_related('cooperative', 'rule').filter(is_resolved=False).order_by('-alert_date')[:5]
        
        # Recent Submissions
        context['recent_submissions'] = submissions.select_related('questionnaire', 'submitted_by').order_by('-submitted_at')[:5]
        
        return context
