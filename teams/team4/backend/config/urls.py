from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from store import views as store_views
from supplements import views as supplement_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "team": "team4",
            "service": "store-supplements-cart",
        }
    )


def whoami(request):
    return JsonResponse(
        {
            "user_id": request.headers.get("X-User-Id", ""),
            "username": request.headers.get("X-User-Username", ""),
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),

    # API infrastructure
    path("api/health/", health_check, name="health"),
    path("api/whoami/", whoami, name="whoami"),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Team 4 APIs
    path("api/store/", include("store.urls")),
    path(
        "api/supplements/",
        include("supplements.urls"),
    ),
    path("api/cart/", include("cart.urls")),

    # Frontend pages
    path(
        "",
        TemplateView.as_view(
            template_name="store/home.html",
        ),
        name="home",
    ),
    path(
        "store/products/",
        TemplateView.as_view(
            template_name="store/products.html",
        ),
        name="products-page",
    ),
    path(
        "store/products/<int:pk>/",
        TemplateView.as_view(
            template_name="store/product_detail.html",
        ),
        name="product-detail-page",
    ),
    path(
        "supplements/<int:pk>/",
        TemplateView.as_view(
            template_name=(
                "supplements/supplement_detail.html"
            ),
        ),
        name="supplement-detail-page",
    ),
    path(
        "cart/",
        TemplateView.as_view(
            template_name="cart/cart.html",
        ),
        name="cart-page",
    ),
    path(
        "checkout/",
        TemplateView.as_view(
            template_name="cart/checkout.html",
        ),
        name="checkout-page",
    ),
    path(
        "orders/",
        TemplateView.as_view(
            template_name="cart/orders.html",
        ),
        name="orders-page",
    ),
    path(
        "login/",
        TemplateView.as_view(
            template_name="store/login.html",
        ),
        name="login-page",
    ),
    path(
        "manage/",
        store_views.admin_dashboard,
        name="admin-dashboard",
    ),
    path(
        "manage/products/",
        store_views.admin_products_page,
    ),
    path(
        "manage/orders/",
        store_views.admin_orders_page,
    ),
    path(
        "manage/discounts/",
        store_views.admin_discounts_page,
    ),
    
    path(
        "manage/supplements/",
        store_views.admin_supplements_page,
    ),
    # path(
    #     "manage/<int:pk>/",
    #     supplement_views.AdminSupplementDetailView.as_view(),
    # ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )