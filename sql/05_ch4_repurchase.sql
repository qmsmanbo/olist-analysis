-- ==========================================================
-- 05 · 第 4 章 复购验证：首单体验对复购的影响
--
-- 前置：01_load_all.sql 已执行
--
-- 口径
--   客户      customer_unique_id（96,096 人），非 customer_id
--   复购      同一客户名下订单数 >= 2
--   观察期    仅取首购 <= 2018-04 的客户，避免右截断
--   体验变量  取首单的超时状态与评分
-- ==========================================================

SET SQL_SAFE_UPDATES = 0;
USE olist;

-- ---------------------------------------------------------------
-- 4.0【基线】客户数、复购客户数、复购率
-- ---------------------------------------------------------------
SELECT COUNT(*)                                       AS 客户数,
       SUM(n >= 2)                                    AS 复购客户,
       ROUND(SUM(n >= 2) * 100.0 / COUNT(*), 2)       AS 复购率
FROM (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS n
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
) t;

-- ---------------------------------------------------------------
-- 4.1【拆单检查】首单到第二单的间隔
-- ---------------------------------------------------------------
WITH x AS (
    SELECT c.customer_unique_id,
           o.order_purchase_timestamp AS ts,
           LAG(o.order_purchase_timestamp)
               OVER (PARTITION BY c.customer_unique_id
                     ORDER BY o.order_purchase_timestamp) AS prev_ts,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id
                              ORDER BY o.order_purchase_timestamp) AS rn
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
)
SELECT COUNT(*)                                                    AS 复购客户数,
       ROUND(AVG(DATEDIFF(ts, prev_ts)), 1)                        AS 间隔均值天,
       ROUND(AVG(CASE WHEN DATEDIFF(ts, prev_ts) <= 1  THEN 1 ELSE 0 END) * 100, 2) AS 一天内占比,
       ROUND(AVG(CASE WHEN DATEDIFF(ts, prev_ts) <= 7  THEN 1 ELSE 0 END) * 100, 2) AS 七天内占比,
       ROUND(AVG(CASE WHEN DATEDIFF(ts, prev_ts) <= 30 THEN 1 ELSE 0 END) * 100, 2) AS 三十天内占比
FROM x
WHERE rn = 2;

-- ---------------------------------------------------------------
-- 4.2【右截断】按首购月份的复购率
-- ---------------------------------------------------------------
WITH first_m AS (
    SELECT c.customer_unique_id,
           MIN(o.order_purchase_timestamp) AS first_ts
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
),
orders_n AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS n
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
)
SELECT DATE_FORMAT(f.first_ts, '%Y-%m')                  AS 首购月,
       COUNT(*)                                          AS 客户数,
       SUM(n.n >= 2)                                     AS 复购人数,
       ROUND(SUM(n.n >= 2) * 100.0 / COUNT(*), 2)        AS 复购率
FROM first_m f
JOIN orders_n n ON n.customer_unique_id = f.customer_unique_id
GROUP BY 首购月
ORDER BY 首购月;

-- ---------------------------------------------------------------
-- 4.3【核心】首单体验 × 是否复购
-- ---------------------------------------------------------------
WITH base AS (
    SELECT c.customer_unique_id,
           o.order_id,
           o.order_purchase_timestamp AS ts,
           DATEDIFF(o.order_delivered_customer_date,
                    o.order_estimated_delivery_date) AS late,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id
                              ORDER BY o.order_purchase_timestamp) AS rn
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
),
f AS (SELECT * FROM base WHERE rn = 1),
orders_n AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS n
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
)
SELECT CASE WHEN f.late > 0 THEN '超时' ELSE '准时' END            AS 时效,
       CASE WHEN r.score <= 2 THEN '差评(1-2)'
            WHEN r.score >= 4 THEN '好评(4-5)'
            ELSE                   '中评(3)' END                  AS 评价,
       COUNT(*)                                                   AS 客户数,
       ROUND(AVG(CASE WHEN n.n >= 2 THEN 1 ELSE 0 END) * 100, 2)  AS 复购率
FROM f
JOIN orders_n n ON n.customer_unique_id = f.customer_unique_id
LEFT JOIN (SELECT order_id, AVG(review_score) AS score
           FROM order_reviews GROUP BY order_id) r ON r.order_id = f.order_id
WHERE DATE_FORMAT(f.ts, '%Y-%m') <= '2018-04'
GROUP BY 时效, 评价
ORDER BY 时效, 评价;
