"""Административный интерфейс для справочников и аудита."""
from django.contrib import admin

from .models import Product, Stock, StockMovement, Warehouse

admin.site.register(Product)
admin.site.register(Warehouse)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity")
    readonly_fields = ("product", "warehouse", "quantity")
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(StockMovement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "warehouse", "kind", "quantity", "created_by")
    readonly_fields = ("product", "warehouse", "kind", "quantity", "created_by", "created_at", "note")
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        return False
