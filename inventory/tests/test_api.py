"""Тесты складских операций API и проверки прав доступа."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from inventory.models import Product, Stock, StockMovement, Warehouse


@pytest.fixture
def staff(db):
    """Создать сотрудника с правом выполнения складских операций."""
    return get_user_model().objects.create_user(
        username="operator",
        password="safe-test-password",
        is_staff=True,
    )


@pytest.fixture
def client_staff(staff):
    """Создать API-клиент, авторизованный как сотрудник."""
    client = APIClient()
    client.force_authenticate(user=staff)
    return client


@pytest.fixture
def sample(db):
    """Создать тестовый товар и склад."""
    product = Product.objects.create(
        sku="PHONE-001",
        name="Телефон",
    )

    warehouse = Warehouse.objects.create(
        code="MSK",
        name="Основной",
    )

    return product, warehouse


@pytest.mark.django_db
def test_receipt_and_issue(client_staff, sample):
    """Поступление и списание правильно изменяют остаток."""
    product, warehouse = sample

    url = "/api/v1/movements/"

    base = {
        "product": product.pk,
        "warehouse": warehouse.pk,
        "quantity": 10,
    }

    # Принимаем на склад 10 единиц товара.
    receipt_response = client_staff.post(
        url,
        {**base, "kind": "receipt"},
    )

    assert receipt_response.status_code == 201

    # Списываем 4 единицы.
    issue_response = client_staff.post(
        url,
        {
            **base,
            "kind": "issue",
            "quantity": 4,
        },
    )

    assert issue_response.status_code == 201

    # После двух операций должно остаться 6 единиц.
    stock = Stock.objects.get(
        product=product,
        warehouse=warehouse,
    )

    assert stock.quantity == 6

    # Обе успешные операции должны быть в журнале.
    assert StockMovement.objects.count() == 2


@pytest.mark.django_db
def test_insufficient_stock_does_not_change_history(
    client_staff,
    sample,
):
    """Списание отсутствующего товара не создаёт остаток и журнал."""
    product, warehouse = sample

    # Товар ещё ни разу не поступал на склад.
    response = client_staff.post(
        "/api/v1/movements/",
        {
            "product": product.pk,
            "warehouse": warehouse.pk,
            "quantity": 1,
            "kind": "issue",
        },
    )

    # Списание должно быть отклонено.
    assert response.status_code == 400

    # Неудачная операция не создаёт пустой остаток.
    assert not Stock.objects.filter(
        product=product,
        warehouse=warehouse,
    ).exists()

    # Неудачная операция не попадает в журнал.
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_insufficient_existing_stock(client_staff, sample):
    """Нельзя списать больше товара, чем есть на складе."""
    product, warehouse = sample

    # Создаём остаток в 3 единицы.
    Stock.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=3,
    )

    # Пытаемся списать 5 единиц.
    response = client_staff.post(
        "/api/v1/movements/",
        {
            "product": product.pk,
            "warehouse": warehouse.pk,
            "quantity": 5,
            "kind": "issue",
        },
    )

    assert response.status_code == 400

    # Количество должно остаться прежним.
    stock = Stock.objects.get(
        product=product,
        warehouse=warehouse,
    )

    assert stock.quantity == 3

    # Ошибочное списание не должно попасть в журнал.
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_non_staff_cannot_create_movement(sample):
    """Обычный пользователь не может выполнять складские операции."""
    product, warehouse = sample

    user = get_user_model().objects.create_user(
        username="viewer",
        password="safe-test-password",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/movements/",
        {
            "product": product.pk,
            "warehouse": warehouse.pk,
            "quantity": 5,
            "kind": "receipt",
        },
    )

    # Доступ к изменению остатков должен быть запрещён.
    assert response.status_code == 403

    # Запрещённая операция не должна изменять данные.
    assert Stock.objects.count() == 0
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_cannot_read_products():
    """Неавторизованный пользователь не получает список товаров."""
    client = APIClient()

    response = client.get("/api/v1/products/")

    # В зависимости от настроек аутентификации:
    # 401 — требуется авторизация;
    # 403 — доступ запрещён.
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_invalid_quantity(client_staff, sample):
    """Нельзя выполнить поступление с нулевым количеством."""
    product, warehouse = sample

    response = client_staff.post(
        "/api/v1/movements/",
        {
            "product": product.pk,
            "warehouse": warehouse.pk,
            "quantity": 0,
            "kind": "receipt",
        },
    )

    assert response.status_code == 400

    # Неправильная операция не изменяет базу.
    assert Stock.objects.count() == 0
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_movement_cannot_be_modified_or_deleted(client_staff, sample):
    """Существующее движение нельзя изменить или удалить через API."""
    product, warehouse = sample

    # Создаём реальное поступление через API.
    response = client_staff.post(
        "/api/v1/movements/",
        {
            "product": product.pk,
            "warehouse": warehouse.pk,
            "quantity": 10,
            "kind": "receipt",
        },
    )

    assert response.status_code == 201

    movement = StockMovement.objects.get()
    url = f"/api/v1/movements/{movement.pk}/"

    # Проверяем запрет редактирования и удаления.
    assert client_staff.put(url, {"quantity": 20}).status_code == 405
    assert client_staff.patch(url, {"quantity": 20}).status_code == 405
    assert client_staff.delete(url).status_code == 405

    # Убеждаемся, что данные не изменились.
    movement.refresh_from_db()
    assert movement.quantity == 10

    stock = Stock.objects.get(product=product, warehouse=warehouse)
    assert stock.quantity == 10

    assert StockMovement.objects.count() == 1