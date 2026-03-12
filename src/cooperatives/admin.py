from django.contrib import admin
from .models import Cooperative, Member, Farm, ProductionRecord, FinancialRecord

@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'region', 'establishment_date')
    search_fields = ('name', 'registration_number')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'member_id', 'is_marginalized', 'is_board_member', 'cooperative', 'gender', 'age_group')
    list_filter = ('gender', 'age_group', 'is_marginalized', 'is_board_member', 'cooperative')
    search_fields = ('first_name', 'last_name', 'member_id')

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('member', 'farm_name', 'size_hectares')
    search_fields = ('farm_name', 'member__last_name')

@admin.register(ProductionRecord)
class ProductionRecordAdmin(admin.ModelAdmin):
    list_display = ('farm', 'crop_type', 'harvest_date', 'quantity_kg', 'quality_grade')
    list_filter = ('crop_type', 'quality_grade')

@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('cooperative', 'transaction_type', 'amount', 'transaction_date')
    list_filter = ('transaction_type',)
