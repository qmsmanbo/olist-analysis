-- ==========================================================
-- 01 · 建库、建表与数据导入
--
-- 一键执行：删库 -> 建 8 张表 -> 导入 9 个 CSV -> 校验
--
-- 前置条件
--   · 连接参数需包含 OPT_LOCAL_INFILE=1，并重连后生效
--   · mysql 全局变量 local_infile = 1
--
-- 表结构要点
--   · order_reviews 使用 (review_id, order_id) 复合主键：源数据中
--     review_id 有 789 个重复（同一评价关联多个订单），单列主键会丢失 814 行
--   · orders 的 4 个日期字段可为空，导入阶段按字符串接收后转 DATETIME
--   · 下游文件依赖 order_wide 宽表，见第 02 号脚本
--
-- 使用前
--   把下面 8 处 :DATA_DIR 替换为本机数据目录的绝对路径（用正斜杠），例如
--     D:/data/olist
--   在 Workbench 里用 Ctrl+H 查找 :DATA_DIR 替换，一次改完
-- ==========================================================

-- 关掉安全更新模式，否则不带主键条件的 UPDATE 会报 1175
SET SQL_SAFE_UPDATES = 0;
SET GLOBAL local_infile = 1;
SET NAMES utf8mb4;

-- 删库重来
DROP DATABASE IF EXISTS olist;
CREATE DATABASE olist DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE olist;

-- 建表（8 张）

CREATE TABLE orders (
  order_id                       VARCHAR(50)  NOT NULL,
  customer_id                    VARCHAR(50)  NOT NULL,
  order_status                   VARCHAR(20)  NULL,
  order_purchase_timestamp       DATETIME     NULL,
  order_approved_at              DATETIME     NULL,
  order_delivered_carrier_date   DATETIME     NULL,
  order_delivered_customer_date  DATETIME     NULL,
  order_estimated_delivery_date  DATETIME     NULL,
  PRIMARY KEY (order_id),
  KEY idx_customer (customer_id),
  KEY idx_purchase (order_purchase_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_items (
  order_id            VARCHAR(50)   NOT NULL,
  order_item_id       INT           NOT NULL,
  product_id          VARCHAR(50)   NULL,
  seller_id           VARCHAR(50)   NULL,
  shipping_limit_date DATETIME      NULL,
  price               DECIMAL(12,2) NULL,
  freight_value       DECIMAL(12,2) NULL,
  PRIMARY KEY (order_id, order_item_id),
  KEY idx_product (product_id),
  KEY idx_seller (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_payments (
  order_id             VARCHAR(50)   NOT NULL,
  payment_sequential   INT           NOT NULL,
  payment_type         VARCHAR(30)   NULL,
  payment_installments INT           NULL,
  payment_value        DECIMAL(12,2) NULL,
  PRIMARY KEY (order_id, payment_sequential)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_reviews (
  review_id               VARCHAR(50) NOT NULL,
  order_id                VARCHAR(50) NOT NULL,
  review_score            INT         NULL,
  review_comment_title    TEXT        NULL,
  review_comment_message  TEXT        NULL,
  review_creation_date    DATETIME    NULL,
  review_answer_timestamp DATETIME    NULL,
  PRIMARY KEY (review_id, order_id),
  KEY idx_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE customers (
  customer_id              VARCHAR(50) NOT NULL,
  customer_unique_id       VARCHAR(50) NULL,
  customer_zip_code_prefix INT         NULL,
  customer_city            VARCHAR(80) NULL,
  customer_state           VARCHAR(10) NULL,
  PRIMARY KEY (customer_id),
  KEY idx_unique (customer_unique_id),
  KEY idx_state (customer_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE products (
  product_id                 VARCHAR(50) NOT NULL,
  product_category_name      VARCHAR(100) NULL,
  product_name_lenght        INT NULL,
  product_description_lenght INT NULL,
  product_photos_qty         INT NULL,
  product_weight_g           INT NULL,
  product_length_cm          INT NULL,
  product_height_cm          INT NULL,
  product_width_cm           INT NULL,
  PRIMARY KEY (product_id),
  KEY idx_cat (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sellers (
  seller_id              VARCHAR(50) NOT NULL,
  seller_zip_code_prefix INT         NULL,
  seller_city            VARCHAR(80) NULL,
  seller_state           VARCHAR(10) NULL,
  PRIMARY KEY (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_category_name_translation (
  product_category_name         VARCHAR(100) NOT NULL,
  product_category_name_english VARCHAR(100) NULL,
  PRIMARY KEY (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 第 2 步：导入
--  LF 文件用 '\n'，CRLF 文件（reviews / translation）用预处理后的 clean 版本
-- ==========================================================

-- 2.1 orders（99,441）—— 4 个日期列有空字符串，先转 NULL 再恢复类型
ALTER TABLE orders
  MODIFY order_approved_at             VARCHAR(30),
  MODIFY order_delivered_carrier_date  VARCHAR(30),
  MODIFY order_delivered_customer_date VARCHAR(30),
  MODIFY order_estimated_delivery_date VARCHAR(30);

LOAD DATA LOCAL INFILE ':DATA_DIR/olist_orders_dataset.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, customer_id, order_status, order_purchase_timestamp,
 @a, @b, @c, order_estimated_delivery_date)
SET order_approved_at             = NULLIF(@a, ''),
    order_delivered_carrier_date  = NULLIF(@b, ''),
    order_delivered_customer_date = NULLIF(@c, '');

ALTER TABLE orders
  MODIFY order_approved_at             DATETIME,
  MODIFY order_delivered_carrier_date  DATETIME,
  MODIFY order_delivered_customer_date DATETIME,
  MODIFY order_estimated_delivery_date DATETIME;

-- 2.2 order_items（112,650）
LOAD DATA LOCAL INFILE ':DATA_DIR/olist_order_items_dataset.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value);

-- 2.3 order_payments（103,886）
LOAD DATA LOCAL INFILE ':DATA_DIR/olist_order_payments_dataset.csv'
INTO TABLE order_payments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, payment_sequential, payment_type, payment_installments, payment_value);

-- 2.4 order_reviews（99,224）—— 用预处理后的 clean 文件，只含 5 列
LOAD DATA LOCAL INFILE ':DATA_DIR/clean/reviews_clean.csv'
INTO TABLE order_reviews
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(review_id, order_id, review_score, review_creation_date, review_answer_timestamp);

-- 2.5 customers（99,441）
LOAD DATA LOCAL INFILE ':DATA_DIR/olist_customers_dataset.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state);

-- 2.6 products（32,951）
LOAD DATA LOCAL INFILE ':DATA_DIR/olist_products_dataset.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_id, @cat, product_name_lenght, product_description_lenght,
 product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)
SET product_category_name = NULLIF(@cat, '');

-- 2.7 sellers（3,095）
LOAD DATA LOCAL INFILE ':DATA_DIR/olist_sellers_dataset.csv'
INTO TABLE sellers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(seller_id, seller_zip_code_prefix, seller_city, seller_state);

-- 2.8 品类翻译（71）—— 用预处理后的 clean 文件
LOAD DATA LOCAL INFILE ':DATA_DIR/clean/translation_clean.csv'
INTO TABLE product_category_name_translation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_category_name, product_category_name_english);

-- 2.9 补齐官方翻译表缺的 2 个品类（补完 translation = 73 行）
INSERT IGNORE INTO product_category_name_translation
  (product_category_name, product_category_name_english)
VALUES
  ('pc_gamer', 'pc_gamer'),
  ('portateis_cozinha_e_preparadores_de_alimentos', 'portable_kitchen_food_preparers');

-- 校验（6 个结果，全部要匹配）

-- 3.1 行数（8 行，实际必须等于期望）
SELECT 'orders'          AS 表名, COUNT(*) AS 实际, 99441  AS 期望 FROM orders
UNION ALL SELECT 'order_items',    COUNT(*), 112650 FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*), 103886 FROM order_payments
UNION ALL SELECT 'order_reviews',  COUNT(*),  99224 FROM order_reviews
UNION ALL SELECT 'customers',      COUNT(*),  99441 FROM customers
UNION ALL SELECT 'products',       COUNT(*),  32951 FROM products
UNION ALL SELECT 'sellers',        COUNT(*),   3095 FROM sellers
UNION ALL SELECT 'translation',    COUNT(*),     73 FROM product_category_name_translation;

-- 3.2 空日期（160 / 1783 / 2965）
SELECT SUM(order_approved_at IS NULL)             AS 未批准,
       SUM(order_delivered_carrier_date IS NULL)  AS 未交承运,
       SUM(order_delivered_customer_date IS NULL) AS 未送达
FROM orders;

-- 3.3 评分分布（11424 / 3151 / 8179 / 19142 / 57328）
SELECT review_score, COUNT(*) AS n FROM order_reviews
GROUP BY review_score ORDER BY review_score;

-- 3.4 品类名不能带回车（必须是 0）
SELECT COUNT(*) AS 带回车符的品类名
FROM product_category_name_translation
WHERE INSTR(product_category_name_english, CHAR(13)) > 0;

-- 3.5 品类翻译能不能 JOIN 上（应该只剩 NULL 品类那 610 个商品）
SELECT COUNT(*) AS 未匹配到英文名的商品
FROM products p
LEFT JOIN product_category_name_translation t
       ON t.product_category_name = p.product_category_name
WHERE p.product_category_name IS NOT NULL
  AND t.product_category_name IS NULL;

-- 3.6 时间范围（2016-09-04 ~ 2018-10-17）
SELECT MIN(order_purchase_timestamp) AS 最早, MAX(order_purchase_timestamp) AS 最晚
FROM orders;
