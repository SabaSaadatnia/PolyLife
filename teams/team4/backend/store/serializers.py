from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent", "children"]

    def get_children(self, obj):
        # دسته‌های زیرمجموعه را برمی‌گرداند
        children = obj.children.filter(is_deleted=False)
        return CategorySerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """برای لیست محصولات - اطلاعات خلاصه"""
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "stock_quantity",
            "brand", "sport_type", "rating", "image_url",
            "category", "category_name", "supplement_id",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """برای صفحه محصول - اطلاعات کامل"""
    category_name = serializers.CharField(source="category.name", read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock_quantity",
            "in_stock",
            "brand",
            "sport_type",
            "rating",
            "image_url",
            "category",
            "category_name",
            "supplement_id",
            "is_active",
            "created_at",
        ]

    extra_kwargs = {
        "slug": {
            "required": False,
            "allow_blank": True,
        }
    }

    def get_in_stock(self, obj):
        return obj.stock_quantity > 0
    
    def create(self, validated_data):
        from django.utils.text import slugify
        from .models import Product

        if not validated_data.get("slug"):
            base_slug = slugify(validated_data["name"])
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            validated_data["slug"] = slug

        return super().create(validated_data)


class ProductWriteSerializer(serializers.ModelSerializer):
    """برای مدیر - ویرایش محصول (FR5)"""
    class Meta:
        model = Product
        fields = [
            "name", "slug", "description", "price",
            "stock_quantity", "category", "brand",
            "sport_type", "image_url", "supplement_id", "is_active",
        ]
