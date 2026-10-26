"""Проверка ограничений целостности базы данных."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from inventory.models import Product, StockMovement, Warehouse


@pytest.mark.django_db
def test_movement_rejects_invalid_kind():
    """База данных запрещает неизвестный тип складской операции."""
    product = Product.objects.create(
        sku="CONSTRAINT-001",
        name="Тестовый товар",
    )
    warehouse = Warehouse.objects.create(
        code="CONSTRAINT",
        name="Тестовый склад",
    )
    user = get_user_model().objects.create_user(
        username="constraint_operator",
        password="safe-test-password",
    )

    # Напрямую обращаемся к ORM, минуя API и сериализатор.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                kind="invalid",
                quantity=1,
                created_by=user,
            )

    # Некорректная операция не должна сохраниться.
    assert StockMovement.objects.count() == 0



@pytest.mark.django_db
def test_admin_cannot_modify_stock_movement():
    """Django Admin запрещает создание, изменение и удаление движений."""
    from django.contrib import admin
    from django.test import RequestFactory

    from inventory.admin import MovementAdmin

    admin_user = get_user_model().objects.create_superuser(
        username="admin_audit_test",
        email="admin@example.com",
        password="test-password-123",
    )

    request = RequestFactory().get("/admin/inventory/stockmovement/")
    request.user = admin_user

    movement_admin = MovementAdmin(StockMovement, admin.site)

    assert movement_admin.has_add_permission(request) is False
    assert movement_admin.has_change_permission(request) is False
    assert movement_admin.has_delete_permission(request) is False