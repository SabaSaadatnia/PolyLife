from django.urls import path

from . import views

# urlpatterns = [
#     path(
#         "",
#         views.SupplementListView.as_view(),
#         name="supplement-list",
#     ),
#     path(
#         "<int:pk>/",
#         views.SupplementDetailView.as_view(),
#         name="supplement-detail",
#     ),
#     path(
#         "<int:pk>/buy/",
#         views.supplement_store_link,
#         name="supplement-store-link",
#     ),
#     path(
#         "admin/",
#         views.AdminSupplementListCreateView.as_view(),
#     ),

#     path(
#         "admin/<int:pk>/",
#         views.AdminSupplementDetailView.as_view(),
#     ),
# ]

urlpatterns = [

    path(
        "admin/",
        views.AdminSupplementListCreateView.as_view(),
    ),

    path(
        "admin/<int:pk>/",
        views.AdminSupplementDetailView.as_view(),
    ),


    path(
        "",
        views.SupplementListView.as_view(),
    ),

    path(
        "<int:pk>/",
        views.SupplementDetailView.as_view(),
    ),

    path(
        "<int:pk>/buy/",
        views.supplement_store_link,
    ),
]