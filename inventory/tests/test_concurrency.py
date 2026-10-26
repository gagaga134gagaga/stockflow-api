"""Проверка конкурентных складских операций на PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from rest_framework.exceptions import ValidationError

from inventory.models import Product, Stock, StockMovement, Warehouse
from inventory.services import apply_movement


@pytest.mark.django_db(transaction=True)
def test_concurrent_issue_does_not_overdraw_stock():
    """Два параллельных списания не могут создать отрицательный остаток."""
    product = Product.objects.create(
        sku="CONCURRENT-001",
        name="Тестовый товар",
    )
    warehouse = Warehouse.objects.create(
        code="TEST",
        name="Тестовый склад",
    )
    user = get_user_model().objects.create_user(
        username="concurrent_operator",
        password="safe-test-password",
        is_staff=True,
    )

    Stock.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=10,
    )

    # Оба потока начинают выполнение складской операции
    # после того, как будут готовы.
    barrier = Barrier(2)

    def issue_stock():
        close_old_connections()

        try:
            barrier.wait(timeout=10)

            apply_movement(
                product=product,
                warehouse=warehouse,
                kind=StockMovement.Kind.ISSUE,
                quantity=7,
                user=user,
            )
            return "success"

        except ValidationError:
            return "rejected"

        finally:
            connections.close_all()

    # Два потока используют отдельные подключения к PostgreSQL.
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(issue_stock)
            for _ in range(2)
        ]
        results = [future.result(timeout=20) for future in futures]

    # Только одно списание должно пройти успешно.
    assert sorted(results) == ["rejected", "success"]

    stock = Stock.objects.get(
        product=product,
        warehouse=warehouse,
    )

    assert stock.quantity == 3

    assert StockMovement.objects.filter(
        product=product,
        warehouse=warehouse,
        kind=StockMovement.Kind.ISSUE,
    ).count() == 1