from django.contrib import admin

from .models import (
    Buyer, Cooperative, CooperativeCertificate, CooperativeSale,
    Farm, FinancialRecord, Member, ProductionRecord, WashingStation,
)


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "region", "establishment_date")
    search_fields = ("name", "registration_number")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "member_id",
        "farmer_code",
        "is_marginalized",
        "is_board_member",
        "is_active",
        "cooperative",
        "gender",
        "age_group",
    )
    list_filter = ("gender", "age_group", "is_marginalized", "is_board_member", "is_active", "cooperative")
    search_fields = ("first_name", "last_name", "member_id", "farmer_code")


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("member", "farm_name", "size_hectares")
    search_fields = ("farm_name", "member__last_name")


class ProductionRecordInline(admin.TabularInline):
    model = ProductionRecord
    extra = 0
    fields = (
        "record_type",
        "member",
        "purchase_date",
        "quantity_kg",
        "base_price_fc",
        "total_price_fc",
        "receipt_number",
    )
    readonly_fields = ("total_price_fc",)


@admin.register(WashingStation)
class WashingStationAdmin(admin.ModelAdmin):
    list_display = ("name", "cooperative", "village", "is_active")
    list_filter = ("cooperative", "is_active")
    search_fields = ("name", "village")
    inlines = [ProductionRecordInline]


@admin.register(ProductionRecord)
class ProductionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "record_type",
        "station",
        "member",
        "farm",
        "crop_type",
        "purchase_date",
        "harvest_date",
        "quantity_kg",
        "total_price_fc",
    )
    list_filter = ("record_type", "crop_type", "station")
    readonly_fields = ("sync_uuid", "total_price_fc")

    fieldsets = (
        (
            "Generic production",
            {
                "fields": (
                    "farm",
                    "crop_type",
                    "harvest_date",
                    "quantity_kg",
                    "quality_grade",
                )
            },
        ),
        (
            "Cherry delivery details",
            {
                "fields": (
                    "station",
                    "member",
                    "record_type",
                    "purchase_date",
                    "reception_date",
                    "receipt_number",
                    "base_price_fc",
                    "total_price_fc",
                    "exchange_rate_fc_usd",
                    "cherry_register_number",
                    "delivery_report_number",
                )
            },
        ),
        (
            "Sync metadata",
            {
                "fields": (
                    "sync_uuid",
                    "is_locally_created",
                )
            },
        ),
    )


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "transaction_type", "amount", "transaction_date")
    list_filter = ("transaction_type",)


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "email", "phone")
    search_fields = ("name", "country")


@admin.register(CooperativeCertificate)
class CooperativeCertificateAdmin(admin.ModelAdmin):
    list_display = ("name", "cooperative", "issuer", "issued_date", "expires_date")
    list_filter = ("cooperative",)
    search_fields = ("name", "issuer")


@admin.register(CooperativeSale)
class CooperativeSaleAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "buyer", "year", "grade", "destination_country", "quantity_kg", "total_value")
    list_filter = ("year", "grade", "destination_country")
    search_fields = ("cooperative__name", "buyer__name")
