from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Product, ProcessLog, Encargada


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("tracking:products")

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            return redirect("tracking:products")

    return render(request, "tracking/login.html")


# =========================
# LOGOUT
# =========================
@login_required
def logout_view(request):
    logout(request)
    return redirect("tracking:login")


# =========================
# SUBQUERY ÚLTIMO PROCESO
# =========================
def last_process_subquery():
    return ProcessLog.objects.filter(
        product=OuterRef("pk")
    ).order_by("-created_at")


# =========================
# PRODUCTOS + FILTROS
# =========================
@login_required
def products(request):
    last_process = last_process_subquery()

    products = (
        Product.objects
        .annotate(
            last_status=Subquery(last_process.values("status")[:1]),
            last_encargada_id=Subquery(last_process.values("assigned_to__id")[:1]),
        )
        .exclude(last_status="VENDIDO") 
        .order_by("-created_at")
    )

    status = request.GET.get("status")
    encargada = request.GET.get("encargada")
    size = request.GET.get("size")
    product_type = request.GET.get("product_type")

    if status:
        products = products.filter(last_status=status)
    if encargada:
        products = products.filter(last_encargada_id=encargada)
    if size:
        products = products.filter(size=size)
    if product_type:
        products = products.filter(product_type__icontains=product_type)

    rows = []
    for p in products:
        rows.append({
            "product": p,
            "status": p.last_status,
            "encargada": Encargada.objects.filter(id=p.last_encargada_id).first(),
        })

    return render(
        request,
        "tracking/products.html",
        {
            "rows": rows,
            "status_choices": ProcessLog.STATUS_CHOICES,
            "encargadas": Encargada.objects.all(),
            "sizes": Product.objects.values_list("size", flat=True).distinct(),
            "filters": request.GET,
            "total": products.count(),
        },
    )


# =========================
# CREAR PRODUCTO
# =========================
@login_required
def product_create(request):
    if request.method == "POST":
        product = Product.objects.create(
            code=request.POST["code"],
            product_type=request.POST["product_type"],
            variant=request.POST.get("variant", ""),
            size=request.POST.get("size", ""),
        )

        ProcessLog.objects.create(
            product=product,
            status=request.POST["status"],
            assigned_to_id=request.POST["encargada"],
            date_out=request.POST.get("fecha_salida") or date.today(),
            date_in=request.POST.get("fecha_llegada") or None,
            comment=request.POST.get("comment", "Creación inicial"),
        )

        return redirect("tracking:products")

    return render(
        request,
        "tracking/product_create.html",
        {
            "encargadas": Encargada.objects.all(),
            "status_choices": ProcessLog.STATUS_CHOICES,
        },
    )


# =========================
# FICHA PRODUCTO
# =========================
@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    history = product.processes.order_by("-created_at")
    current = history.first()

    return render(
        request,
        "tracking/product_detail.html",
        {
            "product": product,
            "history": history,
            "current": current,
            "status_choices": ProcessLog.STATUS_CHOICES,
            "encargadas": Encargada.objects.all(),
        },
    )


# =========================
# AGREGAR PROCESO
# =========================
@require_POST
@login_required
def api_add_process(request, pk):
    product = get_object_or_404(Product, pk=pk)

    ProcessLog.objects.create(
        product=product,
        status=request.POST["status"],
        assigned_to_id=request.POST["encargada"],
        date_out=request.POST["fecha_salida"],
        date_in=request.POST.get("fecha_llegada") or None,
        comment=request.POST.get("comment", ""),
    )

    return JsonResponse({"ok": True})


# =========================
# EDITAR PROCESO
# =========================
@require_POST
@login_required
def api_update_process(request, pk):
    log = get_object_or_404(ProcessLog, pk=pk)

    log.status = request.POST["status"]
    log.assigned_to_id = request.POST["encargada"]
    log.date_out = request.POST["fecha_salida"]
    log.date_in = request.POST.get("fecha_llegada") or None
    log.comment = request.POST.get("comment", "")
    log.save()

    return JsonResponse({"ok": True})


# =========================
# ELIMINAR PROCESO
# =========================
@require_POST
@login_required
def api_delete_process(request, pk):
    log = get_object_or_404(ProcessLog, pk=pk)
    log.delete()
    return JsonResponse({"ok": True})


# =========================
# ELIMINAR PRODUCTO
# =========================
@require_POST
@login_required
def api_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return JsonResponse({"ok": True})


# =========================
# EDITAR PRODUCTO (SIN HISTORIAL)
# =========================
@require_POST
@login_required
def api_update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    product.product_type = request.POST["product_type"]
    product.variant = request.POST.get("variant", "")
    product.size = request.POST.get("size", "")
    product.save()

    return JsonResponse({"ok": True})


# =========================
# LLENADOS
# =========================
@login_required
def llenados(request):
    last_process = last_process_subquery()

    products = (
        Product.objects
        .annotate(
            last_status=Subquery(last_process.values("status")[:1]),
            last_encargada_id=Subquery(last_process.values("assigned_to__id")[:1]),
        )
        .filter(last_status="LLENADO")
        .order_by("-created_at")
    )

    # =========================
    # FILTROS
    # =========================
    encargada = request.GET.get("encargada")
    size = request.GET.get("size")
    product_type = request.GET.get("product_type")

    if encargada:
        products = products.filter(last_encargada_id=encargada)

    if size:
        products = products.filter(size=size)

    if product_type:
        products = products.filter(product_type__icontains=product_type)

    return render(
        request,
        "tracking/llenados.html",
        {
            # productos filtrados
            "products": products,

            # opciones de filtros
            "encargadas": Encargada.objects.all(),
            "sizes": Product.objects.values_list("size", flat=True).distinct(),

            # valores seleccionados (para mantener estado del filtro)
            "filters": request.GET,
        },
    )


# =========================
# VENDIDOS + FILTROS
# =========================
@login_required
def vendidos(request):
    last_process = last_process_subquery()

    products = (
        Product.objects
        .annotate(
            last_status=Subquery(last_process.values("status")[:1]),
            last_encargada_id=Subquery(last_process.values("assigned_to__id")[:1]),
        )
        .filter(last_status="VENDIDO")
        .order_by("-created_at")
    )

    # -------- FILTROS --------
    encargada = request.GET.get("encargada")
    size = request.GET.get("size")
    product_type = request.GET.get("product_type")

    if encargada:
        products = products.filter(last_encargada_id=encargada)

    if size:
        products = products.filter(size=size)

    if product_type:
        products = products.filter(product_type__icontains=product_type)

    rows = []
    for p in products:
        rows.append({
            "product": p,
            "encargada": Encargada.objects.filter(id=p.last_encargada_id).first(),
        })

    return render(
        request,
        "tracking/vendidos.html",
        {
            "rows": rows,
            "encargadas": Encargada.objects.all(),
            "sizes": Product.objects.values_list("size", flat=True).distinct(),
            "filters": request.GET,
            "total": products.count(),
        },
    )


# =========================
# PROCESS LOGS
# =========================
@login_required
def process_logs(request):
    logs = ProcessLog.objects.select_related(
        "product", "assigned_to"
    ).order_by("-created_at")

    return render(request, "tracking/process_logs.html", {"logs": logs})






# =========================
# PARA EXPORTAR EN CSV
# =========================

import csv
from django.http import HttpResponse


@login_required
def export_products_csv(request):
    last_process = last_process_subquery()

    products = (
        Product.objects
        .annotate(
            last_status=Subquery(last_process.values("status")[:1]),
            last_encargada=Subquery(last_process.values("assigned_to__name")[:1]),
            last_date_out=Subquery(last_process.values("date_out")[:1]),
            last_date_in=Subquery(last_process.values("date_in")[:1]),
        )
        .order_by("-created_at")
    )

    # -------- aplicar mismos filtros que products() --------
    status = request.GET.get("status")
    encargada = request.GET.get("encargada")
    size = request.GET.get("size")
    product_type = request.GET.get("product_type")

    if status:
        products = products.filter(last_status=status)

    if encargada:
        products = products.filter(processes__assigned_to_id=encargada)

    if size:
        products = products.filter(size=size)

    if product_type:
        products = products.filter(product_type__icontains=product_type)

    # -------- CSV --------
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="productos_fluxa.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow([
        "Código",
        "Producto",
        "Variante",
        "Medida",
        "Estado actual",
        "Encargada actual",
        "Fecha salida",
        "Fecha llegada",
    ])

    for p in products:
        writer.writerow([
            p.code,
            p.product_type,
            p.variant,
            p.size,
            p.last_status or "",
            p.last_encargada or "",
            p.last_date_out or "",
            p.last_date_in or "",
        ])

    return response
