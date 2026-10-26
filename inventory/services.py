"""Бизнес-логика складских операций.

Здесь находятся правила изменения остатков товаров.
HTTP-запросы обрабатываются отдельно, в представлениях API.
"""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from .models import Product, Stock, StockMovement, Warehouse


@transaction.atomic
def apply_movement(
    *,
    product: Product,
    warehouse: Warehouse,
    kind: str,
    quantity: int,
    user,
    note: str = "",
) -> StockMovement:
    """Выполнить складскую операцию и записать её в журнал.

    Поступление увеличивает остаток, списание уменьшает.

    Изменение остатка и создание записи в журнале выполняются
    в одной транзакции. Если возникает ошибка, изменения
    откатываются.

    select_for_update() блокирует существующую строку остатка,
    чтобы параллельные запросы не изменяли её одновременно.
    """

    # Количество товара должно быть положительным.
    if quantity <= 0:
        raise ValidationError(
            {"quantity": "Количество должно быть больше нуля."}
        )

    # Разрешаем только предусмотренные типы операций.
    if kind not in StockMovement.Kind.values:
        raise ValidationError(
            {"kind": "Неизвестный тип операции."}
        )

    # Неактивные товары нельзя принимать или списывать.
    if not product.is_active:
        raise ValidationError(
            {"product": "Товар неактивен."}
        )

    if kind == StockMovement.Kind.ISSUE:
        # СПИСАНИЕ

        # Ищем существующий остаток и блокируем его строку.
        # Новую запись при списании создавать не нужно.
        stock = (
            Stock.objects.select_for_update()
            .filter(
                product=product,
                warehouse=warehouse,
            )
            .first()
        )

        # Если остатка нет или товара недостаточно,
        # отклоняем операцию.
        if stock is None or stock.quantity < quantity:
            raise ValidationError(
                {"quantity": "Недостаточно товара на складе."}
            )

        # Уменьшаем количество товара.
        stock.quantity -= quantity

    else:
        # ПОСТУПЛЕНИЕ

        # При первом поступлении записи остатка ещё может не быть.
        # get_or_create() создаёт её при необходимости.
        try:
            with transaction.atomic():
                Stock.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={"quantity": 0},
                )

        except IntegrityError:
            # Другая транзакция могла создать такую запись
            # одновременно с нашей.
            # После этого попробуем получить существующую строку.
            pass

        # Блокируем остаток перед изменением количества.
        stock = Stock.objects.select_for_update().get(
            product=product,
            warehouse=warehouse,
        )

        # Увеличиваем количество товара.
        stock.quantity += quantity

    # Сохраняем только изменённое поле.
    stock.save(update_fields=["quantity"])

    # Записываем успешную операцию в журнал.
    # Если создание записи завершится ошибкой,
    # транзакция откатит и изменение остатка.
    movement = StockMovement.objects.create(
        product=product,
        warehouse=warehouse,
        kind=kind,
        quantity=quantity,
        created_by=user,
        note=note,
    )

    return movement