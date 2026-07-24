from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from cart.models import DiscountCode, Invoice, Order, OrderItem, Transaction
from store.models import Category, Product
from supplements.models import Supplement


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_client(user_id: int = 1) -> APIClient:
    c = APIClient()
    c.credentials(HTTP_X_USER_ID=str(user_id), HTTP_X_USER_USERNAME=f"user{user_id}")
    return c


def make_category(name="ورزش", slug="sport") -> Category:
    return Category.objects.create(name=name, slug=slug)


def make_product(category, name="Whey Protein", slug="whey", price="500000", stock=10) -> Product:
    return Product.objects.create(
        name=name,
        slug=slug,
        description="توضیح محصول",
        price=Decimal(price),
        stock_quantity=stock,
        category=category,
        brand="BrandX",
        sport_type="bodybuilding",
        rating=Decimal("4.50"),
    )


def make_coupon(code="SAVE20", percent="20.00", max_uses=100) -> DiscountCode:
    return DiscountCode.objects.create(
        code=code,
        discount_percent=Decimal(percent),
        max_uses=max_uses,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. فلوی کامل خرید: افزودن → ویرایش → کد تخفیف → checkout → فاکتور
# ─────────────────────────────────────────────────────────────────────────────

class FullPurchaseFlowTest(TestCase):
    """
    سناریو: کاربر محصولی را به سبد اضافه می‌کند، تعداد را ویرایش می‌کند،
    کد تخفیف اعمال می‌کند، checkout می‌کند و فاکتور دریافت می‌کند.
    """

    def setUp(self):
        cache.clear()
        self.client = make_client(user_id=42)
        cat = make_category()
        self.product = make_product(cat, price="400000", stock=20)
        self.coupon = make_coupon(code="POLY10", percent="10.00")

    def test_full_purchase_flow(self):
        # ۱. افزودن ۳ عدد به سبد
        r = self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 3}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["cart"]["items"][0]["quantity"], 3)

        # ۲. ویرایش به ۵ عدد
        r = self.client.post("/api/cart/update/", {"product_id": self.product.id, "quantity": 5}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["cart"]["items"][0]["quantity"], 5)

        # ۳. پیش‌نمایش کد تخفیف
        r = self.client.post("/api/cart/apply-coupon/", {"code": "POLY10"}, format="json")
        self.assertEqual(r.status_code, 200)
        total = Decimal("400000") * 5  # 2,000,000
        expected_discount = total * Decimal("10") / Decimal("100")  # 200,000
        self.assertEqual(Decimal(r.data["discount_amount"]), expected_discount)
        self.assertEqual(Decimal(r.data["final_total"]), total - expected_discount)

        # ۴. checkout با همان کد
        r = self.client.post("/api/cart/checkout/", {"discount_code": "POLY10"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("invoice_number", r.data)
        self.assertIn("transaction_ref", r.data)
        self.assertEqual(Decimal(r.data["total_paid"]), Decimal("1800000.00"))

        # ۵. بررسی DB
        order = Order.objects.get()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(order.user_id, 42)
        self.assertEqual(order.final_amount, Decimal("1800000.00"))
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 1)

        # ۶. موجودی کاهش یافته باشد
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

        # ۷. استفاده از کوپن ثبت شده باشد
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.used_count, 1)

        # ۸. سبد پاک شده باشد
        r = self.client.get("/api/cart/")
        self.assertEqual(r.data["items"], [])

    def test_invoice_retrievable_after_checkout(self):
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 1}, format="json")
        r = self.client.post("/api/cart/checkout/", {}, format="json")
        self.assertEqual(r.status_code, 201)

        inv_num = r.data["invoice_number"]
        r2 = self.client.get(f"/api/cart/invoices/{inv_num}/")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["invoice_number"], inv_num)
        self.assertEqual(r2.data["order"]["status"], Order.STATUS_PAID)
        self.assertEqual(len(r2.data["order"]["items"]), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. جداسازی سبد بین کاربران مختلف
# ─────────────────────────────────────────────────────────────────────────────

class CartIsolationTest(TestCase):
    """
    سبد خرید هر کاربر باید کاملاً از بقیه جدا باشد.
    """

    def setUp(self):
        cache.clear()
        cat = make_category()
        self.p1 = make_product(cat, name="Product A", slug="pa", price="100000", stock=50)
        self.p2 = make_product(cat, name="Product B", slug="pb", price="200000", stock=50)
        self.user1 = make_client(user_id=1)
        self.user2 = make_client(user_id=2)

    def test_carts_are_isolated(self):
        self.user1.post("/api/cart/add/", {"product_id": self.p1.id, "quantity": 2}, format="json")
        self.user2.post("/api/cart/add/", {"product_id": self.p2.id, "quantity": 5}, format="json")

        r1 = self.user1.get("/api/cart/")
        r2 = self.user2.get("/api/cart/")

        self.assertEqual(len(r1.data["items"]), 1)
        self.assertEqual(r1.data["items"][0]["product_id"], self.p1.id)

        self.assertEqual(len(r2.data["items"]), 1)
        self.assertEqual(r2.data["items"][0]["product_id"], self.p2.id)

    def test_checkout_only_affects_own_cart(self):
        self.user1.post("/api/cart/add/", {"product_id": self.p1.id, "quantity": 1}, format="json")
        self.user2.post("/api/cart/add/", {"product_id": self.p2.id, "quantity": 1}, format="json")

        self.user1.post("/api/cart/checkout/", {}, format="json")

        # سبد user2 دست نخورده باشد
        r2 = self.user2.get("/api/cart/")
        self.assertEqual(len(r2.data["items"]), 1)

        # فقط یک سفارش برای user1 باشد
        self.assertEqual(Order.objects.filter(user_id=1).count(), 1)
        self.assertEqual(Order.objects.filter(user_id=2).count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 3. edge caseهای موجودی انبار
# ─────────────────────────────────────────────────────────────────────────────

class StockEdgeCasesTest(TestCase):
    """
    سناریوهای مرزی موجودی: خرید دقیقاً به اندازه موجودی، خرید بیش از موجودی.
    """

    def setUp(self):
        cache.clear()
        self.client = make_client(user_id=99)
        cat = make_category()
        self.product = make_product(cat, price="50000", stock=3)

    def test_buy_exactly_available_stock(self):
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 3}, format="json")
        r = self.client.post("/api/cart/checkout/", {}, format="json")
        self.assertEqual(r.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0)

    def test_add_to_cart_exceeding_stock_is_rejected(self):
        r = self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 10}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("available_stock", r.data)
        self.assertEqual(r.data["available_stock"], 3)

    def test_checkout_fails_when_stock_drops_between_add_and_checkout(self):
        """
        کاربر ۲ عدد به سبد اضافه می‌کند، اما بین add و checkout موجودی تغییر می‌کند.
        """
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 2}, format="json")

        # کسی دیگری موجودی را کم کرد
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])

        r = self.client.post("/api/cart/checkout/", {}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("stock", r.data.get("error", "").lower())

        # سبد کاربر هنوز دست‌نخورده باشد
        cart_r = self.client.get("/api/cart/")
        self.assertEqual(len(cart_r.data["items"]), 1)

        # هیچ سفارشی ثبت نشده باشد
        self.assertEqual(Order.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. کد تخفیف — edge caseها
# ─────────────────────────────────────────────────────────────────────────────

class CouponEdgeCasesTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = make_client(user_id=7)
        cat = make_category()
        self.product = make_product(cat, price="100000", stock=100)

    def test_expired_coupon_rejected_at_checkout(self):
        from django.utils import timezone
        import datetime
        expired = DiscountCode.objects.create(
            code="OLD20",
            discount_percent=Decimal("20.00"),
            max_uses=100,
            expires_at=timezone.now() - datetime.timedelta(days=1),
        )
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 1}, format="json")
        r = self.client.post("/api/cart/checkout/", {"discount_code": "OLD20"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("expired", r.data["error"].lower())

    def test_maxed_out_coupon_rejected(self):
        full = DiscountCode.objects.create(
            code="FULL",
            discount_percent=Decimal("15.00"),
            max_uses=5,
            used_count=5,
        )
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 1}, format="json")
        r = self.client.post("/api/cart/checkout/", {"discount_code": "FULL"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_checkout_without_coupon_calculates_correctly(self):
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 4}, format="json")
        r = self.client.post("/api/cart/checkout/", {}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Decimal(r.data["total_paid"]), Decimal("400000.00"))

    def test_coupon_code_is_case_insensitive(self):
        make_coupon(code="UPPER10", percent="10.00")
        self.client.post("/api/cart/add/", {"product_id": self.product.id, "quantity": 1}, format="json")
        r = self.client.post("/api/cart/checkout/", {"discount_code": "upper10"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Decimal(r.data["total_paid"]), Decimal("90000.00"))


# ─────────────────────────────────────────────────────────────────────────────
# 5. ارتباط Supplement ↔ Store
# ─────────────────────────────────────────────────────────────────────────────

class SupplementStoreIntegrationTest(TestCase):
    """
    مکمل باید بتواند محصولات فروشگاهی مرتبط خود را برگرداند،
    و فیلتر supplement_id در store هم کار کند.
    """

    def setUp(self):
        self.client = APIClient()
        cat = make_category()

        self.supplement = Supplement.objects.create(
            name="کراتین",
            scientific_name="Creatine Monohydrate",
            description="مکمل قدرتی",
            dosage="۵ گرم روزانه",
            usage_instructions="با آب مصرف کنید",
            benefits="افزایش قدرت",
            side_effects="ناراحتی معده",
            warnings="زیر ۱۸ سال مناسب نیست",
        )

        self.linked_product = make_product(
            cat,
            name="بسته کراتین",
            slug="creatine-pack",
            price="300000",
        )
        self.linked_product.supplement_id = self.supplement.id
        self.linked_product.save(update_fields=["supplement_id"])

        # محصول غیر مرتبط
        make_product(cat, name="دمبل", slug="dumbell", price="200000")

    def test_supplement_buy_link_returns_related_products(self):
        r = self.client.get(f"/api/supplements/{self.supplement.id}/buy/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["store_products"]), 1)
        self.assertEqual(r.data["store_products"][0]["id"], self.linked_product.id)
        self.assertIn("store_url", r.data)

    def test_store_filter_by_supplement_id(self):
        r = self.client.get("/api/store/products/", {"supplement_id": self.supplement.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["name"], "بسته کراتین")

    def test_store_link_excludes_inactive_products(self):
        self.linked_product.is_active = False
        self.linked_product.save(update_fields=["is_active"])

        r = self.client.get(f"/api/supplements/{self.supplement.id}/buy/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["store_products"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. فیلتر و جستجوی محصولات
# ─────────────────────────────────────────────────────────────────────────────

class ProductFilterSearchTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.cat_sport = Category.objects.create(name="ورزشی", slug="sporty")
        self.cat_food = Category.objects.create(name="تغذیه", slug="food")

        Product.objects.create(
            name="Whey Protein Gold",
            slug="whey-gold",
            description="پروتئین وی درجه یک",
            price=Decimal("800000"),
            stock_quantity=5,
            category=self.cat_sport,
            brand="Optimum",
            sport_type="bodybuilding",
            rating=Decimal("4.80"),
        )
        Product.objects.create(
            name="BCAA Powder",
            slug="bcaa",
            description="آمینو اسید شاخه‌دار",
            price=Decimal("300000"),
            stock_quantity=20,
            category=self.cat_food,
            brand="MusclePharm",
            sport_type="endurance",
            rating=Decimal("4.20"),
        )
        Product.objects.create(
            name="Creatine Mono",
            slug="creatine",
            description="کراتین مونوهیدرات",
            price=Decimal("200000"),
            stock_quantity=0,
            category=self.cat_sport,
            brand="Optimum",
            sport_type="bodybuilding",
            rating=Decimal("4.50"),
            is_active=True,
        )

    def test_filter_by_brand(self):
        r = self.client.get("/api/store/products/", {"brand": "Optimum"})
        names = [p["name"] for p in r.data["results"]]
        self.assertIn("Whey Protein Gold", names)
        self.assertIn("Creatine Mono", names)
        self.assertNotIn("BCAA Powder", names)

    def test_filter_by_price_range(self):
        r = self.client.get("/api/store/products/", {"min_price": 250000, "max_price": 500000})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["name"], "BCAA Powder")

    def test_filter_by_min_rating(self):
        r = self.client.get("/api/store/products/", {"min_rating": 4.5})
        names = [p["name"] for p in r.data["results"]]
        self.assertIn("Whey Protein Gold", names)
        self.assertIn("Creatine Mono", names)
        self.assertNotIn("BCAA Powder", names)

    def test_search_by_name(self):
        r = self.client.get("/api/store/products/", {"search": "BCAA"})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["slug"], "bcaa")

    def test_ordering_by_price_asc(self):
        r = self.client.get("/api/store/products/", {"ordering": "price"})
        prices = [Decimal(p["price"]) for p in r.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_ordering_by_rating_desc(self):
        r = self.client.get("/api/store/products/", {"ordering": "-rating"})
        ratings = [Decimal(p["rating"]) for p in r.data["results"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True))


# ─────────────────────────────────────────────────────────────────────────────
# 7. سبد چند محصولی و checkout
# ─────────────────────────────────────────────────────────────────────────────

class MultiProductCartTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client = make_client(user_id=55)
        cat = make_category()
        self.p1 = make_product(cat, name="A", slug="a", price="100000", stock=10)
        self.p2 = make_product(cat, name="B", slug="b", price="250000", stock=10)
        self.p3 = make_product(cat, name="C", slug="c", price="50000", stock=5)

    def test_cart_total_with_multiple_products(self):
        self.client.post("/api/cart/add/", {"product_id": self.p1.id, "quantity": 2}, format="json")
        self.client.post("/api/cart/add/", {"product_id": self.p2.id, "quantity": 1}, format="json")
        self.client.post("/api/cart/add/", {"product_id": self.p3.id, "quantity": 3}, format="json")

        r = self.client.get("/api/cart/")
        # 2×100k + 1×250k + 3×50k = 200k + 250k + 150k = 600k
        self.assertEqual(Decimal(r.data["total"]), Decimal("600000.00"))
        self.assertEqual(len(r.data["items"]), 3)

    def test_checkout_creates_correct_order_items(self):
        self.client.post("/api/cart/add/", {"product_id": self.p1.id, "quantity": 2}, format="json")
        self.client.post("/api/cart/add/", {"product_id": self.p2.id, "quantity": 1}, format="json")

        r = self.client.post("/api/cart/checkout/", {}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(OrderItem.objects.count(), 2)

        # هر دو محصول موجودی‌شان کم شده باشد
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, 8)
        self.assertEqual(self.p2.stock_quantity, 9)

    def test_order_history_contains_all_items(self):
        self.client.post("/api/cart/add/", {"product_id": self.p1.id, "quantity": 1}, format="json")
        self.client.post("/api/cart/add/", {"product_id": self.p3.id, "quantity": 2}, format="json")
        self.client.post("/api/cart/checkout/", {}, format="json")

        r = self.client.get("/api/cart/orders/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(len(r.data[0]["items"]), 2)


# ─────────────────────────────────────────────────────────────────────────────
# 8. دسته‌بندی سلسله‌مراتبی
# ─────────────────────────────────────────────────────────────────────────────

class CategoryHierarchyTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.root = Category.objects.create(name="ورزش", slug="sport-root")
        self.child1 = Category.objects.create(name="مکمل", slug="supplement-cat", parent=self.root)
        self.child2 = Category.objects.create(name="تجهیزات", slug="equipment-cat", parent=self.root)
        self.grandchild = Category.objects.create(name="پروتئین", slug="protein-cat", parent=self.child1)

    def _categories(self, response):
        """CategoryListView uses pagination → results are under 'results' key."""
        data = response.data
        return data["results"] if "results" in data else list(data)

    def test_category_list_returns_only_roots(self):
        r = self.client.get("/api/store/categories/")
        self.assertEqual(r.status_code, 200)
        names = [c["name"] for c in self._categories(r)]
        self.assertIn("ورزش", names)
        self.assertNotIn("مکمل", names)

    def test_root_category_includes_children(self):
        r = self.client.get("/api/store/categories/")
        root_data = next(c for c in self._categories(r) if c["name"] == "ورزش")
        child_names = [c["name"] for c in root_data["children"]]
        self.assertIn("مکمل", child_names)
        self.assertIn("تجهیزات", child_names)

    def test_deleted_subcategory_is_hidden(self):
        self.child2.is_deleted = True
        self.child2.save()

        r = self.client.get("/api/store/categories/")
        root_data = next(c for c in self._categories(r) if c["name"] == "ورزش")
        child_names = [c["name"] for c in root_data["children"]]
        self.assertNotIn("تجهیزات", child_names)
        self.assertIn("مکمل", child_names)


# ─────────────────────────────────────────────────────────────────────────────
# 9. share link و health check
# ─────────────────────────────────────────────────────────────────────────────

class UtilityEndpointsTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        cat = make_category()
        self.product = make_product(cat)

    def test_health_check(self):
        r = self.client.get("/api/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertEqual(r.json()["team"], "team4")

    def test_share_link_contains_product_id(self):
        r = self.client.get(f"/api/store/products/{self.product.id}/share/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["product_id"], self.product.id)
        self.assertIn(str(self.product.id), r.data["share_url"])

    def test_share_link_for_nonexistent_product(self):
        r = self.client.get("/api/store/products/99999/share/")
        self.assertEqual(r.status_code, 404)

    def test_whoami_returns_user_headers(self):
        c = make_client(user_id=7)
        r = c.get("/api/whoami/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["user_id"], "7")

    def test_invoice_of_other_user_is_forbidden(self):
        """کاربر نباید فاکتور کاربر دیگری را ببیند."""
        cache.clear()
        owner = make_client(user_id=10)
        cat = make_category(name="Cat2", slug="cat2")
        p = make_product(cat, name="P2", slug="p2")
        owner.post("/api/cart/add/", {"product_id": p.id, "quantity": 1}, format="json")
        r = owner.post("/api/cart/checkout/", {}, format="json")
        inv_num = r.data["invoice_number"]

        intruder = make_client(user_id=99)
        r2 = intruder.get(f"/api/cart/invoices/{inv_num}/")
        self.assertEqual(r2.status_code, 404)
