"""Тонкий HTTP-слой: маршрутизация, права доступа, фильтрация."""
from rest_framework import mixins, permissions, viewsets

from .models import Product, Stock, StockMovement, Warehouse
from .serializers import (
    MovementSerializer,
    ProductSerializer,
    StockSerializer,
    WarehouseSerializer,
)


class StaffWritePermission(permissions.BasePermission):
    """Чтение доступно авторизованным; изменение — только сотрудникам."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.method in permissions.SAFE_METHODS or request.user.is_staff
        ))

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [StaffWritePermission]

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by("id")
    serializer_class = WarehouseSerializer
    permission_classes = [StaffWritePermission]

class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related("product", "warehouse").order_by("id")
    serializer_class = StockSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("warehouse"):
            queryset = queryset.filter(warehouse_id=self.request.query_params["warehouse"])
        if self.request.query_params.get("product"):
            queryset = queryset.filter(product_id=self.request.query_params["product"])
        return queryset

class MovementViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = StockMovement.objects.select_related("product", "warehouse", "created_by")
    serializer_class = MovementSerializer
    permission_classes = [StaffWritePermission]
