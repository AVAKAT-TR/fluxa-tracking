from django.contrib import admin
from django.db.models import OuterRef, Subquery
from django.contrib.admin import SimpleListFilter
from .models import (
    Product,
    ProductoLlenado,
    ProductoVendido,
    ProcessLog,
    Encargada,
)

# =====================================================
# FILTROS PERSONALIZADOS
# =====================================================
class EstadoActualFilter(SimpleListFilter):
    title = "Estado actual"
    parameter_name = "estado_actual"

    def lookups(self, request, model_admin):
        return ProcessLog.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(last_status=self.value())
        return queryset


class EncargadaActualFilter(SimpleListFilter):
    title = "Encargada actual"
    parameter_name = "encargada_actual"

    def lookups(self, request, model_admin):
        return [(e.name, e.name) for e in Encargada.objects.filter(active=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(last_encargada=self.value())
        return queryset


# =========================
# ENCARGADAS
# =========================
@admin.register(Encargada)
class EncargadaAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


# =========================
# PROCESS LOG (HISTORIAL)
# =========================
@admin.register(ProcessLog)
class ProcessLogAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "status",
        "assigned_to",
        "date_out",
        "date_in",
        "short_comment",
    )
    list_filter = ("status", "assigned_to", "date_out")
    search_fields = ("product__code", "assigned_to__name", "comment")
    date_hierarchy = "date_out"
    ordering = ("-date_out",)

    def short_comment(self, obj):
        return obj.comment[:40] if obj.comment else "-"
    short_comment.short_description = "Comentario"


# =========================
# INLINE
# =========================
class ProcessLogInline(admin.TabularInline):
    model = ProcessLog
    extra = 0
    autocomplete_fields = ("assigned_to",)
    fields = ("status", "assigned_to", "date_out", "date_in", "comment")


# =====================================================
# BASE ADMIN PARA PRODUCTOS
# =====================================================
class ProductBaseAdmin(admin.ModelAdmin):
    search_fields = ("code", "product_type")
    ordering = ("-created_at",)
    inlines = [ProcessLogInline]

    list_display = (
        "code",
        "product_type",
        "variant",
        "size",
        "estado_actual",
        "encargada_actual",
        "created_at",
    )

    list_filter = (
        EstadoActualFilter,
        EncargadaActualFilter,
    )

    @admin.display(description="Estado")
    def estado_actual(self, obj):
        return obj.last_status if obj.last_status else "-"

    @admin.display(description="Encargada")
    def encargada_actual(self, obj):
        return obj.last_encargada if obj.last_encargada else "-"

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        last_log = ProcessLog.objects.filter(
            product=OuterRef("pk")
        ).order_by("-created_at")

        return qs.annotate(
            last_status=Subquery(last_log.values("status")[:1]),
            last_encargada=Subquery(last_log.values("assigned_to__name")[:1]),
        )


# =========================
# PRODUCTS (EN PROCESO)
# =========================
@admin.register(Product)
class ProductAdmin(ProductBaseAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(last_status__in=["LLENADO", "VENDIDO"])


# =========================
# LLENADOS
# =========================
@admin.register(ProductoLlenado)
class LlenadosAdmin(ProductBaseAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(last_status="LLENADO")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# =========================
# VENDIDOS
# =========================
@admin.register(ProductoVendido)
class VendidosAdmin(ProductBaseAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(last_status="VENDIDO")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False