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