from django.contrib import admin

from .models import Supplement


@admin.register(Supplement)
class SupplementAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "scientific_name",
        "is_deleted",
        "updated_at",
    ]
    list_filter = ["is_deleted"]
    search_fields = [
        "name",
        "scientific_name",
        "description",
        "benefits",
        "warnings",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]