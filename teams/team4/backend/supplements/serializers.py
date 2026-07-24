from rest_framework import serializers
from .models import Supplement


class SupplementListSerializer(serializers.ModelSerializer):
    """لیست خلاصه مکمل‌ها"""
    class Meta:
        model = Supplement
        fields = ["id", "name", "scientific_name", "description"]


class SupplementDetailSerializer(serializers.ModelSerializer):
    """جزئیات کامل علمی مکمل (FR6)"""
    class Meta:
        model = Supplement
        fields = [
            "id", "name", "scientific_name", "description",
            "dosage", "usage_instructions", "benefits",
            "side_effects", "warnings", "fda_reference",
        ]

class SupplementAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplement

        fields = [
            "id",
            "name",
            "scientific_name",
            "description",
            "dosage",
            "usage_instructions",
            "benefits",
            "side_effects",
            "warnings",
            "fda_reference",
            "is_deleted",
        ]