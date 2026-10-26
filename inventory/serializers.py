"""Проверка входных данных и преобразование моделей в JSON."""
from rest_framework import serializers

from .models import Product, Stock, StockMovement, Warehouse
from .services import apply_movement


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "sku", "name", "is_active"]

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name"]

class StockSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)

    class Meta:
        model = Stock
        fields = ["id", "product", "product_sku", "warehouse", "warehouse_code", "quantity"]
        read_only_fields = fields

class MovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id", "product", "warehouse", "kind", "quantity", "note", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def create(self, validated_data):
        """Изменять остатки разрешено только через единую бизнес-операцию."""
        return apply_movement(**validated_data, user=self.context["request"].user)
