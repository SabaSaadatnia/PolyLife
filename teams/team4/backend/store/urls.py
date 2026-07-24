from django.urls import path

from . import views

urlpatterns = [
    path(
        "categories/",
        views.CategoryListView.as_view(),
        name="category-list",
    ),
    path(
        "products/",
        views.ProductListView.as_view(),
        name="product-list",
    ),
    path(
        "products/<int:pk>/",
        views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "products/<int:pk>/share/",
        views.product_share_link,
        name="product-share",
    ),
    path(
        "admin/products/",
        views.AdminProductListCreateView.as_view(),
    ),
    path(
        "admin/products/<int:pk>/",
        views.AdminProductDetailView.as_view(),
    ),
    path(
        "admin/products/<int:pk>/stock/",
        views.AdminStockUpdateView.as_view(),
    ),
    path(
        "manage/",
        views.admin_dashboard,
        name="admin-dashboard",
    ),
    path(
        "manage/products/",
        views.admin_products_page,
        name="admin-products-page",
    ),
    path(
        "manage/orders/",
        views.admin_orders_page,
        name="admin-orders-page",
    ),
    path(
        "manage/discounts/",
        views.admin_discounts_page,
        name="admin-discounts-page",
    ),
]