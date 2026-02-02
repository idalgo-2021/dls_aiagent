-- 1. Справочник моделей
CREATE TABLE IF NOT EXISTS product_models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    brand       TEXT NOT NULL,  -- Nike, Adidas, Puma и т.д.
    model       TEXT NOT NULL,  -- Air Force 1, Ultraboost, RS-X
    description TEXT NOT NULL,  -- описание: для чего подходит, особенности
    UNIQUE (brand, model)       -- одна модель бренда — одна запись
);

-- 2. Создание таблиц (если ещё не созданы)
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    article     TEXT,               -- артикул (уникальный идентификатор модели)
    size        REAL NOT NULL,      -- размер в EU (40.5, 42.0 и т.д.)
    color       TEXT,               -- White, Black, 'Triple Black' и т.д.
    price       INTEGER NOT NULL,   -- цена в основной в USD
    model_id    INTEGER NOT NULL REFERENCES product_models(id)
);

-- 3. Остатки (без изменений)
CREATE TABLE IF NOT EXISTS stock_by_warehouses (
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse   TEXT NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, warehouse)
);

-- 4. Заявки клиентов
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    order_json TEXT,                 -- весь заказ в JSON
    status TEXT DEFAULT 'new'
);

-- 5. Полная очистка перед заполнением
DELETE FROM stock_by_warehouses;
DELETE FROM products;
DELETE FROM product_models;
DELETE FROM orders;
DELETE FROM sqlite_sequence WHERE name IN ('products', 'product_models');

-- 6. Заполнение справочника моделей — 20 уникальных моделей
INSERT OR IGNORE INTO product_models (brand, model, description) VALUES
('Nike',     'Air Force 1 Low',      'Классика streetwear. Универсальные, комфортные. Для города, повседневки, лёгкого спорта.'),
('Nike',     'Air Max 90',           'Икона беговых кроссовок. Отличная амортизация. Для длительной ходьбы и бега по асфальту.'),
('Nike',     'Dunk Low',             'Стильные lifestyle-кроссовки. Для уличной моды, скейтбординга и casual.'),
('Adidas',   'Ultraboost Light',     'Премиум беговые кроссовки. Максимальная амортизация Boost. Для длительных пробежек.'),
('Adidas',   'Samba OG',             'Классика футзала и стритвира. Для города, повседневки, лёгкого спорта.'),
('Adidas',   'Gazelle',              'Ретро-стиль, комфорт на каждый день. Для casual-образа и прогулок.'),
('Puma',     'RS-X3',                'Яркие lifestyle-кроссовки. Для молодёжного стиля, повседневки, уличной моды.'),
('Puma',     'Suede Classic',        'Классика 80-х. Комфортные для города, прогулок, лёгкого спорта.'),
('New Balance', '574 Core',          'Универсальные повседневные кроссовки. Очень комфортные, для длительной ходьбы.'),
('New Balance', '550',               'Ретро-баскетбольный стиль. Для стритвира и casual-образа.'),
('New Balance', '990v6',             'Премиум беговые и повседневные. Отличная амортизация и поддержка.'),
('Vans',     'Old Skool',            'Классика скейт-культуры. Для уличного стиля, повседневки, лёгкого спорта.'),
('Vans',     'Authentic',            'Минималистичные повседневные кроссовки. Лёгкие, удобные на каждый день.'),
('Converse', 'Chuck 70 High',        'Высокие ретро-кеды. Для casual-образа, уличной моды, повседневки.'),
('Converse', 'Run Star Hike',        'Высокие кеды с тракторной подошвой. Для стритвира, прогулок.'),
('Reebok',   'Club C 85',            'Классические теннисные кроссовки. Комфортные для города и повседневки.'),
('Asics',    'Gel-Kayano 14',        'Стабильные беговые кроссовки. Гелевая амортизация, для длительных тренировок.'),
('Asics',    'Gel-1130',             'Ретро-беговые кроссовки. Комфортные для города и лёгкого бега.'),
('Balenciaga','Triple S',            'Массивные дизайнерские кроссовки. Для люксового стритвира и модных образов.'),
('Balenciaga','Track 2',             'Футуристичные кроссовки. Для премиум-стритвира и яркого образа.');

-- 7. Заполнение конкретных товаров (по 2 размера на модель)
INSERT OR IGNORE INTO products (article, size, color, price, model_id)
SELECT
    pm.brand || '-' || REPLACE(pm.model, ' ', '') || '-' || printf('%.1f', s.size) AS article,
    s.size,
    s.color,
    s.price,
    pm.id
FROM product_models pm
CROSS JOIN (
    SELECT 
        34.0 + (abs(random()) % 25) * 0.5 AS size,  -- строго 34.0–46.0 с шагом 0.5
        CASE abs(random()) % 10
            WHEN 0 THEN 'White'
            WHEN 1 THEN 'Black'
            WHEN 2 THEN 'Grey'
            WHEN 3 THEN 'Red'
            WHEN 4 THEN 'Green'
            WHEN 5 THEN 'Blue'
            WHEN 6 THEN 'Navy'
            WHEN 7 THEN 'Multi'
            WHEN 8 THEN 'Pink'
            ELSE 'Yellow'
        END AS color,
        60 + (abs(random()) % 191) AS price  -- 60–250 USD
    FROM product_models LIMIT 2  -- по 2 размера на модель
) s;

-- 8. Заполнение остатков по складам
INSERT OR IGNORE INTO stock_by_warehouses (product_id, warehouse, quantity)
SELECT 
    p.id,
    w.warehouse,
    CASE 
        WHEN abs(random()) % 10 < 2 THEN 0               -- 20% шанс на 0
        ELSE (abs(random()) % 25) + 1                    -- 1–25 штук
    END AS quantity
FROM products p
CROSS JOIN (
    SELECT 'Bishkek' AS warehouse UNION 
    SELECT 'Almaty' UNION 
    SELECT 'Tashkent' UNION 
    SELECT 'Dushanbe' UNION 
    SELECT 'Moscow'
) w
WHERE abs(random()) % 100 < 75;  -- ~75% комбинаций заполнены

-- 9. Проверка результата
SELECT 'Моделей в справочнике: ' || COUNT(*) FROM product_models;
SELECT 'Конкретных артикулов: ' || COUNT(*) FROM products;
SELECT 'Записей о наличии: ' || COUNT(*) FROM stock_by_warehouses;