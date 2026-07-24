from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "parent",
        "is_deleted",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_deleted"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "price",
        "stock_quantity",
        "category",
        "brand",
        "rating",
        "is_active",
        "is_deleted",
    ]
    list_filter = [
        "category",
        "brand",
        "sport_type",
        "is_active",
        "is_deleted",
    ]
    search_fields = ["name", "brand", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = [
        "price",
        "stock_quantity",
        "is_active",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]