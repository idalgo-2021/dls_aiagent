import sqlite3
from smolagents import tool
from typing import Optional
from config import config
import json
from datetime import datetime

DB_PATH = config["database"]["path"]


@tool
def create_order_request(
    user_id: str,
    customer_name: str,
    customer_phone: str,
    items: list[
        dict
    ],  # [{"brand": "...", "model": "...", "size": 43.5, "color": "...", "quantity": 1, "price": 143.0}, ...]
    total_price: float,
    warehouse_preference: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Создаёт предварительную заявку на заказ кроссовок в формате JSON.

    Args:
        user_id: Уникальный идентификатор пользователя (например Telegram ID или "manual_имя_телефон")
        customer_name: Имя клиента
        customer_phone: Телефон клиента для связи с менеджером
        items: Список позиций заказа (каждый элемент — словарь с brand, model, size, color, quantity, price)
        total_price: Общая сумма заказа
        warehouse_preference: Желаемый склад отгрузки (опционально)
        notes: Дополнительные комментарии клиента или агента (опционально)

    Returns:
        str: Подтверждение создания заявки с красивым текстом для клиента
    """
    order_data = {
        "items": items,
        "total_price": total_price,
        "warehouse_preference": warehouse_preference,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }

    order_json = json.dumps(order_data, ensure_ascii=False, indent=2)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (
            user_id, customer_name, customer_phone, order_json
        ) VALUES (?, ?, ?, ?)
        """,
        (user_id, customer_name, customer_phone, order_json),
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    text = f"Заявка #{order_id} создана и отправлена менеджеру!\n\n"
    for item in items:
        text += f"- {item['brand']} {item['model']}, размер {item['size']}"
        if item.get("color"):
            text += f", цвет {item['color']}"
        text += f" — {item['quantity']} шт. по {item['price']} USD\n"
    text += f"\nИтого: {total_price} USD\n"
    if warehouse_preference:
        text += f"Желаемый склад: {warehouse_preference}\n"
    if notes:
        text += f"Комментарий: {notes}\n"
    text += "\nМенеджер свяжется с вами в ближайшее время для подтверждения и оплаты."

    return text
