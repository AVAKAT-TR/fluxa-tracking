from django.db import models


class Encargada(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    product_type = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.product_type} ({self.variant})"

    # ========= ESTADO ACTUAL =========
    @property
    def current_process(self):
        return self.processes.order_by("-created_at").first()

    @property
    def current_status(self):
        process = self.current_process
        return process.status if process else ""

    @property
    def current_encargada(self):
        process = self.current_process
        return process.assigned_to.name if process else ""


class ProcessLog(models.Model):
    STATUS_CHOICES = [
        ("CORTANDO", "Cortando"),
        ("COSIENDO", "Cosiendo"),
        ("COSIDO", "Cosido"),
        ("BORDANDO", "Bordando"),
        ("BORDADO", "Bordado"),
        ("LLENADO", "Llenado"),
        ("VENDIDO", "Vendido"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="processes"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    assigned_to = models.ForeignKey(
        Encargada,
        on_delete=models.PROTECT
    )
    date_out = models.DateField()
    date_in = models.DateField(null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.code} - {self.status}"


# ========= PROXY MODELS =========
class ProductoLlenado(Product):
    class Meta:
        proxy = True
        verbose_name = "Llenado"
        verbose_name_plural = "Llenados"


class ProductoVendido(Product):
    class Meta:
        proxy = True
        verbose_name = "Vendido"
        verbose_name_plural = "Vendidos"
