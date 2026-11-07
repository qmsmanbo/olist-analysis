# -*- coding: utf-8 -*-
"""第 4 章 · 取数：MySQL → output/ch4_*.csv"""
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

PASSWORD = os.environ.get("MYSQL_PWD", "在这里填你的root密码")
if "填" in PASSWORD:
    sys.exit("先设置环境变量 MYSQL_PWD")
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output"
engine = create_engine(
    f"mysql+pymysql://root:{quote_plus(PASSWORD)}@127.0.0.1:3306/olist?charset=utf8mb4",
    pool_pre_ping=True)

# 每个客户的首单（含体验），只看首购 <= 2018-04（保证至少 6 个月观察期）
BASE_SQL = """
WITH u AS (
    SELECT c.customer_unique_id, o.order_id, o.order_purchase_timestamp AS ts,
           DATE_FORMAT(o.order_purchase_timestamp,'%Y-%m') AS month,
           DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date) AS late
    FROM orders o JOIN customers c ON c.customer_id = o.customer_id
),
first_order AS (
    SELECT * FROM (
        SELECT u.*, ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY ts) AS seq
        FROM u
    ) x WHERE seq = 1
),
orders_n AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS n FROM u GROUP BY customer_unique_id
)
SELECT f.customer_unique_id, f.month, f.late,
       r.score, CASE WHEN n.n >= 2 THEN 1 ELSE 0 END AS rp
FROM first_order f
JOIN orders_n n ON n.customer_unique_id = f.customer_unique_id
LEFT JOIN (SELECT order_id, AVG(review_score) AS score FROM order_reviews GROUP BY order_id) r
       ON r.order_id = f.order_id
WHERE f.month <= '2018-04'
"""

df = pd.read_sql(text(BASE_SQL), engine)

# 1) cohort（全部首购月份，不设观察期，用来看右截断）
all_first = pd.read_sql(text(BASE_SQL.replace("WHERE f.month <= '2018-04'", "")), engine)
c = all_first.groupby("month").agg(customers=("rp", "size"), repeat=("rp", "sum"))
c["rate"] = (c.repeat / c.customers * 100).round(2)
c.reset_index().to_csv(OUT / "ch4_cohort.csv", index=False, encoding="utf-8-sig")
print("cohort", len(c), "行")

# 2) 四象限
df["组"] = df.late.apply(lambda x: "超时" if x > 0 else "准时") + "·" + \
           pd.cut(df.score, [0, 2, 3, 5], labels=["差评", "中评", "好评"]).astype(str)
q = df.groupby("组").agg(customers=("rp", "size"), rate=("rp", "mean"))
q["rate"] = (q.rate * 100).round(2)
q.reset_index().to_csv(OUT / "ch4_quad.csv", index=False, encoding="utf-8-sig")
print("四象限", len(q), "行")
print(q)
