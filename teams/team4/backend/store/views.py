from django.urls import reverse
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponseForbidden

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from config.permissions import IsTeam4Admin
# from .serializers import ProductSerializer

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
    )
    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
    )
    min_rating = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="gte",
    )

    class Meta:
        model = Product
        fields = ["category", "brand", "sport_type","supplement_id"]


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            parent=None,
            is_deleted=False,
        ).prefetch_related("children")


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "brand"]
    ordering_fields = ["price", "rating", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            is_deleted=False,
        ).select_related("category")


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            is_deleted=False,
        ).select_related("category")
    
class AdminProductListCreateView(APIView):
    permission_classes = [IsTeam4Admin]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductDetailSerializer(
            products,
            many=True
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductDetailSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=201
            )

        return Response(
            serializer.errors,
            status=400
        )

class AdminStockUpdateView(APIView):
    permission_classes = [IsTeam4Admin]

    def patch(self, request, pk):
        product = Product.objects.filter(id=pk).first()

        if not product:
            return Response(
                {"error": "Product not found"},
                status=404
            )

        stock = request.data.get("stock_quantity")

        if stock is None:
            return Response(
                {"error": "stock_quantity is required"},
                status=400
            )

        try:
            stock = int(stock)
        except ValueError:
            return Response(
                {"error": "stock_quantity must be an integer"},
                status=400
            )

        if stock < 0:
            return Response(
                {"error": "stock cannot be negative"},
                status=400
            )

        product.stock_quantity = stock
        product.save(update_fields=["stock_quantity"])

        return Response(
            {
                "message": "Stock updated successfully",
                "product_id": product.id,
                "stock_quantity": product.stock_quantity
            }
        )
    

class AdminProductDetailView(APIView):
    permission_classes = [IsTeam4Admin]

    def get_object(self, pk):
        return Product.objects.filter(id=pk).first()

    def get(self, request, pk):
        product = self.get_object(pk)

        if not product:
            return Response(
                {"error": "Product not found"},
                status=404
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


    def put(self, request, pk):
        product = self.get_object(pk)

        if not product:
            return Response(
                {"error": "Product not found"},
                status=404
            )

        serializer = ProductDetailSerializer(
            product,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=400
        )


    def delete(self, request, pk):
        product = self.get_object(pk)

        if not product:
            return Response(
                {"error": "Product not found"},
                status=404
            )

        # soft delete instead of removing data
        product.is_active = False
        product.save()

        return Response(
            {
                "message": "Product deactivated successfully"
            }
        )
    
@api_view(["GET"])
def product_share_link(request, pk):
    try:
        product = Product.objects.get(
            pk=pk,
            is_active=True,
            is_deleted=False,
        )
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    product_path = f"/api/store/products/{product.pk}/"

    share_url = request.build_absolute_uri(
        product_path
    )

    return Response(
        {
            "product_id": product.pk,
            "product_name": product.name,
            "share_url": share_url,
        }
    )

def check_admin_page(request):
    username = request.headers.get("X-User-Username", "")
    return username == "admin"


def admin_dashboard(request):
    if not check_admin_page(request):
        return HttpResponseForbidden("Access denied")   
    return render(
        request,
        "store/admin/dashboard.html"
    )
def admin_products_page(request):

    if not check_admin_page(request):
        return HttpResponseForbidden(
            "Access denied"
        )

    return render(
        request,
        "store/admin/products.html"
    )



def admin_orders_page(request):

    if not check_admin_page(request):
        return HttpResponseForbidden(
            "Access denied"
        )

    return render(
        request,
        "store/admin/orders.html"
    )



def admin_discounts_page(request):

    if not check_admin_page(request):
        return HttpResponseForbidden(
            "Access denied"
        )

    return render(
        request,
        "store/admin/discounts.html"
    )

def admin_supplements_page(request):

    if not check_admin_page(request):
        return HttpResponseForbidden(
            """
            <h1>Access Denied</h1>
            <p>You do not have permission to access this page.</p>
            """
        )

    return render(
        request,
        "store/admin/supplements.html"
    )
