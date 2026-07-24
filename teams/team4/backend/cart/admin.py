from django.contrib import admin

from .models import (
    DiscountCode,
    Invoice,
    Order,
    OrderItem,
    Transaction,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = [
        "product",
        "quantity",
        "unit_price",
        "subtotal",
        "created_at",
    ]


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "discount_percent",
        "used_count",
        "max_uses",
        "is_active",
        "expires_at",
        "is_deleted",
    ]
    list_filter = ["is_active", "is_deleted"]
    search_fields = ["code"]
    readonly_fields = ["used_count", "created_at", "updated_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_id",
        "total_amount",
        "discount_amount",
        "final_amount",
        "status",
        "created_at",
    ]
    list_filter = ["status", "is_deleted"]
    search_fields = ["id", "user_id"]
    readonly_fields = [
        "user_id",
        "discount_code",
        "total_amount",
        "discount_amount",
        "final_amount",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_ref",
        "order",
        "amount",
        "status",
        "created_at",
    ]
    list_filter = ["status", "is_deleted"]
    search_fields = ["transaction_ref", "order__id"]
    readonly_fields = [
        "order",
        "transaction_ref",
        "amount",
        "status",
        "gateway_response",
        "created_at",
        "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "user_id",
        "order",
        "created_at",
    ]
    list_filter = ["is_deleted"]
    search_fields = ["invoice_number", "user_id", "order__id"]
    readonly_fields = [
        "order",
        "invoice_number",
        "user_id",
        "created_at",
        "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False