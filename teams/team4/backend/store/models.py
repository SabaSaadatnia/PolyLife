from django.db import models


class Category(models.Model):
    """
    دسته‌بندی سلسله‌مراتبی محصولات (FR1)
    مثال: ورزش > مکمل > پروتئین
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    # parent=None یعنی دسته ریشه است
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "categories"
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["parent"])]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    محصول فروشگاه (FR2, FR3, FR4, FR5)
    """
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
    )
    brand = models.CharField(max_length=200, blank=True, db_index=True)
    sport_type = models.CharField(max_length=200, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    image_url = models.URLField(blank=True)
    image = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True
    )
    # ارتباط با میکروسرویس مکمل (اختیاری - فقط برای محصولات مکمل)
    supplement_id = models.IntegerField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["is_active", "is_deleted"]),
        ]

    def __str__(self):
        return self.name

    def decrease_stock(self, quantity: int):
        """کاهش موجودی انبار (FR4)"""
        if self.stock_quantity < quantity:
            raise ValueError(f"موجودی کافی نیست. موجودی فعلی: {self.stock_quantity}")
        self.stock_quantity -= quantity
        self.save(update_fields=["stock_quantity", "updated_at"])
