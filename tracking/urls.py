from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("products/", views.products, name="products"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/add-process/", views.api_add_process, name="api_add_process"),
    path("products/<int:pk>/update/", views.api_update_product, name="api_update_product"),
    path("products/<int:pk>/delete/", views.api_delete_product, name="api_delete_product"),

    path("process/<int:pk>/update/", views.api_update_process, name="api_update_process"),
    path("process/<int:pk>/delete/", views.api_delete_process, name="api_delete_process"),

    path("llenados/", views.llenados, name="llenados"),
    path("vendidos/", views.vendidos, name="vendidos"),
    path("process-logs/", views.process_logs, name="process_logs"),
    path("products/export/csv/", views.export_products_csv, name="export_products_csv"),

]
