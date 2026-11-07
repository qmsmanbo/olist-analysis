-- ==========================================================
-- 02 · 第 1 章 生意盘子：规模、趋势、结构
--
-- 前置：01_load_all.sql 已执行，order_wide 已建好
--
-- 口径
--   订单范围  order_status = 'delivered'（96,478 单，占全部订单 97%）
--   GMV       SUM(price)，不含运费；运费单列 freight
--   时间窗    2017-01 ~ 2018-08，剔除 2016 年不完整月份与
--             2018-09 之后尚未送达的订单
-- ==========================================================

SET SQL_SAFE_UPDATES = 0;
USE olist;

-- 订单宽表：一单一行，供后续各章复用
-- INNER JOIN 会滤掉 775 个无明细订单（98,666 = 99,441 - 775），均为取消或不可用
-- ==========================================================
DROP TABLE IF EXISTS order_wide;

CREATE TABLE order_wide AS
SELECT o.order_id,
       c.customer_unique_id,
       c.customer_state,
       o.order_status,
       o.order_purchase_timestamp                      AS buy_ts,
       DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS buy_month,
       o.order_delivered_customer_date                 AS delivered_ts,
       o.order_estimated_delivery_date                 AS estimated_ts,
       SUM(oi.price)                                   AS gmv,
       SUM(oi.freight_value)                           AS freight,
       COUNT(*)                                        AS item_cnt
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers   c  ON c.customer_id = o.customer_id
GROUP BY o.order_id, c.customer_unique_id, c.customer_state, o.order_status,
         o.order_purchase_timestamp, o.order_delivered_customer_date,
         o.order_estimated_delivery_date;

ALTER TABLE order_wide
  ADD KEY idx_order (order_id),
  ADD KEY idx_month (buy_month),
  ADD KEY idx_status (order_status);

-- 自查：98,666 行，其中 delivered 96,478
SELECT COUNT(*) AS 宽表行数,
       SUM(order_status = 'delivered') AS 已送达
FROM order_wide;

-- 1.0 整体规模
SELECT COUNT(*)                  AS 订单数,
       ROUND(SUM(gmv), 2)        AS GMV,
       ROUND(SUM(freight), 2)    AS 运费,
       ROUND(SUM(gmv) / COUNT(*), 2)                AS AOV,
       ROUND((SUM(gmv) + SUM(freight)) / COUNT(*), 2) AS AOV含运费
FROM order_wide
WHERE order_status = 'delivered';

-- 1.1 月度趋势
SELECT buy_month                        AS 月份,
       COUNT(*)                         AS 订单数,
       ROUND(SUM(gmv), 2)               AS GMV,
       ROUND(SUM(gmv) / COUNT(*), 2)    AS AOV
FROM order_wide
WHERE order_status = 'delivered'
  AND buy_month BETWEEN '2017-01' AND '2018-08'
GROUP BY buy_month
ORDER BY buy_month;

-- 1.2 州 TOP10
SELECT customer_state                                   AS 州,
       COUNT(*)                                         AS 订单数,
       ROUND(SUM(gmv), 2)                               AS GMV,
       ROUND(SUM(gmv) * 100.0 / SUM(SUM(gmv)) OVER (), 2) AS 占比
FROM order_wide
WHERE order_status = 'delivered'
  AND buy_month BETWEEN '2017-01' AND '2018-08'
GROUP BY customer_state
ORDER BY GMV DESC
LIMIT 10;

-- ==========================================================
-- 查询 1.3【靠什么撑着·品类】品类 TOP10
-- 说明：品类是「明细粒度」的信息，order_wide 是订单粒度，所以这里要回到 order_items
-- ==========================================================
SELECT t.product_category_name_english                     AS 品类,
       COUNT(DISTINCT w.order_id)                          AS 订单数,
       ROUND(SUM(oi.price), 2)                             AS GMV,
       ROUND(SUM(oi.price) * 100.0
             / SUM(SUM(oi.price)) OVER (), 2)              AS 占比
FROM order_wide w
JOIN order_items oi ON oi.order_id = w.order_id
JOIN products    p  ON p.product_id = oi.product_id
LEFT JOIN product_category_name_translation t
       ON t.product_category_name = p.product_category_name
WHERE w.order_status = 'delivered'
  AND w.buy_month BETWEEN '2017-01' AND '2018-08'
GROUP BY t.product_category_name_english
ORDER BY GMV DESC
LIMIT 10;

-- ==========================================================
-- 查询 1.4【靠什么撑着·支付】支付方式分布
-- 说明：一个订单可能多行支付，所以订单数要 COUNT(DISTINCT order_id)
-- ==========================================================
SELECT p.payment_type                                          AS 支付方式,
       COUNT(DISTINCT p.order_id)                              AS 订单数,
       ROUND(SUM(p.payment_value), 2)                          AS 支付金额,
       ROUND(SUM(p.payment_value) * 100.0
             / SUM(SUM(p.payment_value)) OVER (), 2)           AS 金额占比
FROM order_payments p
JOIN order_wide w ON w.order_id = p.order_id
WHERE w.order_status = 'delivered'
  AND w.buy_month BETWEEN '2017-01' AND '2018-08'
GROUP BY p.payment_type
ORDER BY 支付金额 DESC;

-- 1.5 月度相对水平（识别大促月）
WITH m AS (
    SELECT buy_month AS 月份, COUNT(*) AS 订单数, SUM(gmv) AS GMV
    FROM order_wide
    WHERE order_status = 'delivered'
      AND buy_month BETWEEN '2017-01' AND '2018-08'
    GROUP BY buy_month
)
SELECT 月份,
       订单数,
       ROUND(GMV, 2)                                          AS GMV,
       ROUND(订单数 * 100.0 / AVG(订单数) OVER (), 1)          AS 订单相对月均,
       ROUND(GMV    * 100.0 / AVG(GMV)    OVER (), 1)          AS GMV相对月均
FROM m
ORDER BY 订单数 DESC
LIMIT 6;
