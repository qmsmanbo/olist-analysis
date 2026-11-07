-- ==========================================================
-- 03 · 第 2 章 履约质量：配送时长、超时率、地域与时间分布
--
-- 前置：01_load_all.sql 已执行
--
-- 口径
--   样本      delivered 且 delivered_ts 非空（96,470 单；另有 8 单缺送达时间）
--   配送天数  DATEDIFF(delivered_ts, buy_ts)，按整天计算
--   超时      DATEDIFF(delivered_ts, estimated_ts) > 0
--   说明      DATEDIFF 截断到天，超时不足一天不计为超时。
--             若按小时精确计算，超时率为 8.11%（本文件按整天口径为 6.77%）
-- ==========================================================

SET SQL_SAFE_UPDATES = 0;
USE olist;

-- 2.1 整体配送时长与超时率
SELECT COUNT(*)                                          AS 样本,
       ROUND(AVG(days), 2)                               AS 平均天数,
       ROUND(AVG(is_late) * 100, 2)                      AS 超时率,
       ROUND(AVG(CASE WHEN is_late = 1 THEN late_days END), 1)  AS 超时单平均超时天数,
       ROUND(AVG(CASE WHEN is_late = 0 THEN ABS(late_days) END), 1) AS 准时单平均提前天数,
       MAX(days)                                         AS 最长天数
FROM (
    SELECT DATEDIFF(delivered_ts, buy_ts) AS days,
           DATEDIFF(delivered_ts, estimated_ts) AS late_days,
           CASE WHEN DATEDIFF(delivered_ts, estimated_ts) > 0 THEN 1 ELSE 0 END AS is_late
    FROM order_wide
    WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
) t;

-- 2.2 MySQL 没有 PERCENTILE 函数，用行号模拟
WITH x AS (
    SELECT DATEDIFF(delivered_ts, buy_ts) AS days,
           ROW_NUMBER() OVER (ORDER BY DATEDIFF(delivered_ts, buy_ts)) AS rn,
           COUNT(*)     OVER ()                                        AS n
    FROM order_wide
    WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
)
SELECT ROUND(AVG(days), 1) AS 中位数
FROM x
WHERE rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2));

-- 2.3 配送时长分箱（用于绘制分布图）
WITH t AS (
    SELECT DATEDIFF(delivered_ts, buy_ts) AS days
    FROM order_wide
    WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
)
SELECT CASE WHEN days <= 3  THEN '1) 0-3天'
            WHEN days <= 7  THEN '2) 4-7天'
            WHEN days <= 15 THEN '3) 8-15天'
            WHEN days <= 30 THEN '4) 16-30天'
            ELSE                 '5) 30天以上' END          AS 分箱,
       COUNT(*)                                             AS 订单数,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)   AS 占比
FROM t
GROUP BY 分箱
ORDER BY MIN(days);

-- 2.4 分州配送表现（订单数 >= 500 的州）
SELECT customer_state                       AS 州,
       COUNT(*)                             AS 订单数,
       ROUND(AVG(DATEDIFF(delivered_ts, buy_ts)), 2)  AS 平均天数,
       ROUND(AVG(CASE WHEN DATEDIFF(delivered_ts, estimated_ts) > 0
                      THEN 1 ELSE 0 END) * 100, 2)    AS 超时率
FROM order_wide
WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
GROUP BY customer_state
HAVING COUNT(*) >= 500
ORDER BY 订单数 DESC;

-- 2.5 月度配送表现
SELECT buy_month                            AS 月份,
       COUNT(*)                             AS 订单数,
       ROUND(AVG(DATEDIFF(delivered_ts, buy_ts)), 2) AS 平均天数,
       ROUND(AVG(CASE WHEN DATEDIFF(delivered_ts, estimated_ts) > 0
                      THEN 1 ELSE 0 END) * 100, 2)   AS 超时率,
       ROUND(AVG(DATEDIFF(estimated_ts, buy_ts)), 1)  AS 承诺天数
FROM order_wide
WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
  AND buy_month BETWEEN '2017-01' AND '2018-08'
GROUP BY buy_month
ORDER BY buy_month;

-- 2.6 分品类配送表现（件数 Top10）
SELECT t.product_category_name_english      AS 品类,
       COUNT(*)                             AS 件数,
       ROUND(AVG(DATEDIFF(w.delivered_ts, w.buy_ts)), 2) AS 平均天数,
       ROUND(AVG(CASE WHEN DATEDIFF(w.delivered_ts, w.estimated_ts) > 0
                      THEN 1 ELSE 0 END) * 100, 2)   AS 超时率
FROM order_wide w
JOIN order_items oi ON oi.order_id = w.order_id
JOIN products    p  ON p.product_id = oi.product_id
LEFT JOIN product_category_name_translation t
       ON t.product_category_name = p.product_category_name
WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
GROUP BY t.product_category_name_english
ORDER BY 件数 DESC
LIMIT 10;
