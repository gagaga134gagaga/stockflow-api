from rest_framework.routers import DefaultRouter

from .views import MovementViewSet, ProductViewSet, StockViewSet, WarehouseViewSet

router = DefaultRouter()
router.register("products", ProductViewSet)
router.register("warehouses", WarehouseViewSet)
router.register("stocks", StockViewSet, basename="stock")
router.register("movements", MovementViewSet, basename="movement")
urlpatterns = router.urls
