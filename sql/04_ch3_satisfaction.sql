-- ==========================================================
-- 04 · 第 3 章 时效与满意度：评分随超时程度的变化
--
-- 前置：01_load_all.sql 已执行
--
-- 口径
--   样本      已送达且有评价（95,824 单，覆盖率 99.3%）
--   评分      一个订单可能有多条评价（525 单），按订单取 AVG(review_score)
--   差评      review_score <= 2
--   超时      同第 03 号脚本
-- ==========================================================

SET SQL_SAFE_UPDATES = 0;
USE olist;

-- 3.0 整体满意度
SELECT COUNT(*)                                       AS 样本,
       ROUND(AVG(score), 3)                           AS 平均分,
       ROUND(AVG(score >= 4) * 100, 2)                AS 好评率,
       ROUND(AVG(score <= 2) * 100, 2)                AS 差评率,
       ROUND(AVG(score = 1)  * 100, 2)                AS 一星率
FROM (
    SELECT w.order_id,
           AVG(r.review_score)                        AS score
    FROM order_wide w
    JOIN order_reviews r ON r.order_id = w.order_id
    WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
    GROUP BY w.order_id
) t;

-- 3.1 按配送时长分箱看评分
SELECT CASE WHEN days <= 3  THEN '1) 0-3天'
            WHEN days <= 7  THEN '2) 4-7天'
            WHEN days <= 15 THEN '3) 8-15天'
            WHEN days <= 30 THEN '4) 16-30天'
            ELSE                 '5) 30天以上' END        AS 分箱,
       COUNT(*)                                            AS 订单数,
       ROUND(AVG(score), 3)                                AS 平均分,
       ROUND(AVG(score <= 2) * 100, 2)                     AS 差评率
FROM (
    SELECT w.order_id,
           DATEDIFF(w.delivered_ts, w.buy_ts) AS days,
           AVG(r.review_score)                AS score
    FROM order_wide w
    JOIN order_reviews r ON r.order_id = w.order_id
    WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
    GROUP BY w.order_id, days
) t
GROUP BY 分箱 ORDER BY 分箱;

-- ==========================================================
-- 查询 3.2【核心】按「超时程度」分箱看评分 （定位拐点）
-- 这是全篇最重要的一张表：超时的代价是断崖式、而非线性的
-- ==========================================================
SELECT CASE WHEN late <= 0   THEN '1) 准时或提前'
            WHEN late <= 3   THEN '2) 超1-3天'
            WHEN late <= 7   THEN '3) 超4-7天'
            WHEN late <= 15  THEN '4) 超8-15天'
            ELSE                  '5) 超15天以上' END      AS 分箱,
       COUNT(*)                                            AS 订单数,
       ROUND(AVG(score), 3)                                AS 平均分,
       ROUND(AVG(score <= 2) * 100, 2)                     AS 差评率,
       ROUND(AVG(score = 1)  * 100, 2)                     AS 一星率
FROM (
    SELECT w.order_id,
           DATEDIFF(w.delivered_ts, w.estimated_ts) AS late,
           AVG(r.review_score)                     AS score
    FROM order_wide w
    JOIN order_reviews r ON r.order_id = w.order_id
    WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
    GROUP BY w.order_id, late
) t
GROUP BY 分箱 ORDER BY 分箱;

-- ==========================================================
-- 查询 3.3【归因】差评中超时订单的占比
-- 换个说法：超时订单只占样本 6.7%，却贡献了 32.5% 的差评
-- ==========================================================
SELECT CASE WHEN score <= 2 THEN '差评(1-2星)'
            WHEN score >= 4 THEN '好评(4-5星)'
            ELSE                 '中评(3星)' END           AS 类别,
       COUNT(*)                                            AS 订单数,
       SUM(late > 0)                                       AS 其中超时单数,
       ROUND(SUM(late > 0) * 100.0 / COUNT(*), 2)          AS 超时占比
FROM (
    SELECT w.order_id,
           DATEDIFF(w.delivered_ts, w.estimated_ts) AS late,
           AVG(r.review_score)                     AS score
    FROM order_wide w
    JOIN order_reviews r ON r.order_id = w.order_id
    WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
    GROUP BY w.order_id, late
) t
GROUP BY 类别 ORDER BY 类别;

-- ==========================================================
-- 查询 3.4【交叉验证】分州验证超时对评分的影响
-- 目的：排除「偏远州用户本来就更挑剔」这个替代解释
-- ==========================================================
SELECT w.customer_state                                AS 州,
       COUNT(*)                                        AS 订单数,
       ROUND(AVG(CASE WHEN DATEDIFF(w.delivered_ts, w.estimated_ts) <= 0
                      THEN r.review_score END), 3)     AS 准时平均分,
       ROUND(AVG(CASE WHEN DATEDIFF(w.delivered_ts, w.estimated_ts) > 0
                      THEN r.review_score END), 3)     AS 超时平均分
FROM order_wide w
JOIN order_reviews r ON r.order_id = w.order_id
WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
GROUP BY w.customer_state
HAVING COUNT(*) >= 500
ORDER BY 订单数 DESC;
