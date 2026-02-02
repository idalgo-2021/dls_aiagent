import sqlite3
from smolagents import tool
from typing import Optional
from config import config
import json
from collections import defaultdict

DB_PATH = config["database"]["path"]


@tool
def search_models(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    purpose: Optional[str] = None,
) -> str:
    """
    Ищет подходящие модели кроссовок по бренду, модели или назначению.
    Возвращает модели с описанием, общим количеством и детальной разбивкой остатков по складам в JSON.

    Args:
        brand: Бренд (Nike, Adidas и т.д.). Частичное совпадение.
        model: Название модели. Частичное совпадение.
        purpose: Для чего нужны (бег, город, повседневка, тренировки и т.д.).

    Returns:
        str: JSON-массив моделей с остатками по складам (или сообщение об ошибке/отсутствии).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT
        pm.id,
        pm.brand,
        pm.model,
        pm.description,
        COALESCE(SUM(sw.quantity), 0) AS total_stock,
        json_group_object(
            sw.warehouse,
            COALESCE(sw.quantity, 0)
        ) FILTER (WHERE sw.quantity IS NOT NULL) AS stock_by_warehouse_json
    FROM product_models pm
    LEFT JOIN products p ON p.model_id = pm.id
    LEFT JOIN stock_by_warehouses sw ON sw.product_id = p.id
    WHERE 1=1
    """
    params = []

    if brand:
        query += " AND pm.brand LIKE ?"
        params.append(f"%{brand}%")
    if model:
        query += " AND pm.model LIKE ?"
        params.append(f"%{model}%")
    if purpose:
        query += " AND pm.description LIKE ?"
        params.append(f"%{purpose}%")

    query += """
    GROUP BY pm.id
    ORDER BY total_stock DESC
    """

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        conn.close()
        return f"Ошибка базы данных: {e}"

    conn.close()

    if not rows:
        return "Модели по вашему запросу не найдены."

    result = []
    for row in rows:
        pm_id, brand, model_name, description, total_stock, stock_json = row

        stock_by_warehouse = json.loads(stock_json) if stock_json else {}

        model_data = {
            "brand": brand,
            "model": model_name,
            "description": description,
            "total_stock": total_stock,
            "stock_by_warehouse": stock_by_warehouse,
        }
        result.append(model_data)

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_model_details(brand: str, model: str) -> str:
    """
    Возвращает описание конкретной модели кроссовок, общее количество в наличии и разбивку остатков по всем складам (включая нулевые).

    Args:
        brand: Бренд
        model: Название модели

    Returns:
        str: JSON с описанием, общим количеством и остатками по складам (или сообщение "не найдено").
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT
        pm.description,
        COALESCE(SUM(sw.quantity), 0) AS total_stock,
        json_group_object(
            sw.warehouse,
            COALESCE(sw.quantity, 0)
        ) AS stock_by_warehouse_json
    FROM product_models pm
    LEFT JOIN products p ON p.model_id = pm.id
    LEFT JOIN stock_by_warehouses sw ON sw.product_id = p.id
    WHERE pm.brand LIKE ? AND pm.model LIKE ?
    GROUP BY pm.id
    """
    cursor.execute(query, (f"%{brand}%", f"%{model}%"))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Модель не найдена."

    description, total_stock, stock_json = row

    stock_by_warehouse = {}
    if stock_json and stock_json != "null" and stock_json.strip():
        try:
            stock_by_warehouse = json.loads(stock_json)
        except json.JSONDecodeError:
            stock_by_warehouse = {}

    result = {
        "brand": brand,
        "model": model,
        "description": description,
        "total_stock": total_stock,
        "stock_by_warehouse": stock_by_warehouse,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_stock_and_price(
    article: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    size_min: Optional[float] = None,
    size_max: Optional[float] = None,
    color: Optional[str] = None,
    warehouse: Optional[str] = None,
) -> str:
    """
    Показывает цену и наличие кроссовок. Поддерживает диапазон размеров через size_min и size_max.

    Args:
        article: Артикул (самый точный поиск)
        brand: Бренд (Nike, Adidas и т.д.). Частичное совпадение.
        model: Модель (Air Force 1 Low и т.д.). Частичное совпадение.
        size_min: Нижняя граница размера EU (например 43.0)
        size_max: Верхняя граница размера EU (например 44.0)
        color: Цвет (White, Black и т.д.). Частичное совпадение.
        warehouse: Склад (если указан — только по нему)

    Returns:
        str: JSON с найденными товарами, ценами и наличием по складам (или текст для человека, если JSON не нужен).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        p.article,
        pm.brand,
        pm.model,
        p.size,
        p.color,
        p.price,
        s.warehouse,
        COALESCE(s.quantity, 0) AS quantity
    FROM products p
    JOIN product_models pm ON p.model_id = pm.id
    LEFT JOIN stock_by_warehouses s ON s.product_id = p.id
    WHERE 1=1
    """
    params = []

    if article:
        query += " AND p.article = ?"
        params.append(article)
    if brand:
        query += " AND pm.brand LIKE ?"
        params.append(f"%{brand}%")
    if model:
        query += " AND pm.model LIKE ?"
        params.append(f"%{model}%")
    if size_min is not None and size_max is not None:
        query += " AND p.size BETWEEN ? AND ?"
        params.extend([size_min, size_max])
    elif size_min is not None:
        query += " AND p.size = ?"
        params.append(size_min)
    if color:
        query += " AND p.color LIKE ?"
        params.append(f"%{color}%")
    if warehouse:
        query += " AND s.warehouse = ?"
        params.append(warehouse)

    query += " ORDER BY p.article, p.size, s.warehouse"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        conn.close()
        return f"Ошибка базы данных: {e}"

    conn.close()

    if not rows:
        return json.dumps(
            {"error": "Товаров по вашему запросу не найдено."},
            ensure_ascii=False,
            indent=2,
        )

    grouped = defaultdict(list)
    for row in rows:
        key = (
            row["article"],
            row["brand"],
            row["model"],
            row["size"],
            row["color"],
            row["price"],
        )
        grouped[key].append((row["warehouse"], row["quantity"]))

    items = []
    total_stock_all = 0
    stock_summary = defaultdict(int)

    for key, stocks in grouped.items():
        article, brand, model, size, color, price = key
        item_stock = sum(qty for _, qty in stocks)
        total_stock_all += item_stock

        item = {
            "article": article,
            "brand": brand,
            "model": model,
            "size": size,
            "color": color,
            "price": price,
            "stock_by_warehouse": {wh: qty for wh, qty in stocks},
            "total_item_stock": item_stock,
        }
        items.append(item)

        for wh, qty in stocks:
            stock_summary[wh] += qty

    result = {
        "brand": brand if brand else "Разные",
        "model": model if model else "Разные",
        "items": items,
        "total_stock_all": total_stock_all,
        "stock_by_warehouse_summary": dict(stock_summary),
    }

    json_output = json.dumps(result, ensure_ascii=False, indent=2)

    text_lines = []
    for item in items:
        line = f"{item['brand']} {item['model']} ({item['size']} EU"
        if item["color"]:
            line += f", {item['color']}"
        line += f") — {item['price']} USD"
        text_lines.append(line)
        text_lines.append("Наличие:")
        for wh, qty in item["stock_by_warehouse"].items():
            text_lines.append(f"  {wh}: {qty} шт.")
        text_lines.append("")

    text_output = "\n".join(text_lines) or "Нет данных по складам."

    return json_output + "\n\n[Человекочитаемый текст для справки]:\n" + text_output
