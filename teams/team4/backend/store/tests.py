from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product


class StoreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            name="Supplements",
            slug="supplements",
        )

        self.product = Product.objects.create(
            name="Whey Protein",
            slug="whey-protein",
            description="Protein supplement",
            price=Decimal("500000.00"),
            stock_quantity=10,
            category=self.category,
            brand="Brand A",
            sport_type="bodybuilding",
            rating=Decimal("4.50"),
            supplement_id=1,
        )

    def test_product_list_returns_active_product(self):
        response = self.client.get("/api/store/products/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["name"],
            "Whey Protein",
        )

    def test_product_filter_by_brand(self):
        response = self.client.get(
            "/api/store/products/",
            {"brand": "Brand A"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_product_filter_by_supplement_id(self):
        response = self.client.get(
            "/api/store/products/",
            {"supplement_id": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_deleted_product_is_hidden(self):
        self.product.is_deleted = True
        self.product.save()

        response = self.client.get("/api/store/products/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_product_detail_reports_stock(self):
        response = self.client.get(
            f"/api/store/products/{self.product.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["in_stock"])

    def test_share_link_is_generated(self):
        response = self.client.get(
            f"/api/store/products/{self.product.id}/share/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["product_id"],
            self.product.id,
        )
        self.assertIn(
            "/store/products/",
            response.data["share_url"]
        )