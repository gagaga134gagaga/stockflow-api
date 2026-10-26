"""Справочники, текущие остатки и неизменяемый журнал движения товара."""
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Product(models.Model):
    """Товар с уникальным артикулом (SKU)."""
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} — {self.name}"

class Warehouse(models.Model):
    """Физический склад, на котором хранятся товары."""
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Stock(models.Model):
    """Текущий остаток конкретного товара на конкретном складе."""
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stocks")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stocks")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "warehouse"], name="unique_product_warehouse")]

class StockMovement(models.Model):
    """Аудит операций поступления и списания товара."""
    class Kind(models.TextChoices):
        RECEIPT = "receipt", "Поступление"
        ISSUE = "issue", "Списание"

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name="movement_positive_quantity")]
