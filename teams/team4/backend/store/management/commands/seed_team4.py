from decimal import Decimal

from django.core.management.base import BaseCommand

from cart.models import DiscountCode
from store.models import Category, Product
from supplements.models import Supplement


class Command(BaseCommand):
    help = "Create Team 4 Persian demo data."

    def handle(self, *args, **options):

        supplements_category, _ = Category.objects.update_or_create(
            slug="supplements",
            defaults={
                "name": "مکمل‌ها",
                "description": "مکمل‌های ورزشی",
                "is_deleted": False,
            },
        )

        equipment_category, _ = Category.objects.update_or_create(
            slug="equipment",
            defaults={
                "name": "تجهیزات ورزشی",
                "description": "تجهیزات مورد نیاز تمرین",
                "is_deleted": False,
            },
        )

        protein_category, _ = Category.objects.update_or_create(
            slug="protein-supplements",
            defaults={
                "name": "مکمل‌های پروتئینی",
                "parent": supplements_category,
                "description": "مکمل‌های پروتئینی برای ورزشکاران",
                "is_deleted": False,
            },
        )

        creatine, _ = Supplement.objects.update_or_create(
            name="کراتین مونوهیدرات",
            defaults={
                "scientific_name": "Creatine Monohydrate",
                "description": (
                    "مکملی محبوب برای افزایش قدرت و بهبود عملکرد "
                    "در تمرینات با شدت بالا."
                ),
                "dosage": "۳ تا ۵ گرم در روز.",
                "usage_instructions": (
                    "روزانه همراه با آب مصرف شود."
                ),
                "benefits": (
                    "کمک به افزایش قدرت، توان و عملکرد ورزشی."
                ),
                "side_effects": (
                    "ممکن است باعث احتباس آب یا ناراحتی گوارشی شود."
                ),
                "warnings": (
                    "در صورت داشتن شرایط پزشکی خاص با پزشک مشورت کنید."
                ),
                "fda_reference": (
                    "اطلاعات آموزشی است و توصیه پزشکی محسوب نمی‌شود."
                ),
                "is_deleted": False,
            },
        )

        whey, _ = Supplement.objects.update_or_create(
            name="پروتئین وی",
            defaults={
                "scientific_name": "Whey Protein Concentrate",
                "description": (
                    "پروتئین استخراج شده از شیر برای تامین نیاز پروتئینی."
                ),
                "dosage": "۲۰ تا ۳۰ گرم در هر وعده.",
                "usage_instructions": (
                    "با آب یا شیر مخلوط کرده و مصرف کنید."
                ),
                "benefits": (
                    "کمک به تامین پروتئین روزانه و ریکاوری عضلات."
                ),
                "side_effects": (
                    "در افراد حساس به لاکتوز ممکن است ناراحتی گوارشی ایجاد کند."
                ),
                "warnings": (
                    "برای افراد دارای حساسیت به پروتئین شیر مناسب نیست."
                ),
                "fda_reference": (
                    "اطلاعات آموزشی است و توصیه پزشکی محسوب نمی‌شود."
                ),
                "is_deleted": False,
            },
        )

        Product.objects.update_or_create(
            slug="whey-protein-1kg",
            defaults={
                "name": "پروتئین وی ۱ کیلوگرم",
                "description": (
                    "بسته یک کیلوگرمی پروتئین وی."
                ),
                "price": Decimal("1850000.00"),
                "stock_quantity": 25,
                "category": protein_category,
                "brand": "PolyLife",
                "sport_type": "بدنسازی",
                "rating": Decimal("4.50"),
                "supplement_id": whey.id,
                "is_active": True,
                "is_deleted": False,
            },
        )

        Product.objects.update_or_create(
            slug="creatine-300g",
            defaults={
                "name": "کراتین ۳۰۰ گرم",
                "description": (
                    "بسته کراتین مونوهیدرات."
                ),
                "price": Decimal("950000.00"),
                "stock_quantity": 30,
                "category": supplements_category,
                "brand": "PolyLife",
                "sport_type": "تمرین قدرتی",
                "rating": Decimal("4.70"),
                "supplement_id": creatine.id,
                "is_active": True,
                "is_deleted": False,
            },
        )

        Product.objects.update_or_create(
            slug="exercise-mat",
            defaults={
                "name": "مت ورزشی",
                "description": (
                    "مت ضد لغزش مناسب تمرین در منزل."
                ),
                "price": Decimal("650000.00"),
                "stock_quantity": 20,
                "category": equipment_category,
                "brand": "PolyLife",
                "sport_type": "فیتنس",
                "rating": Decimal("4.20"),
                "supplement_id": None,
                "is_active": True,
                "is_deleted": False,
            },
        )

        DiscountCode.objects.update_or_create(
            code="SALAM10",
            defaults={
                "discount_percent": Decimal("10.00"),
                "max_uses": 100,
                "is_active": True,
                "is_deleted": False,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Team 4 Persian demo data created successfully."
            )
        )