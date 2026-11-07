# -*- coding: utf-8 -*-
"""第 2 章 · 取数：MySQL → output/ch2_*.csv"""
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

USER = "root"
PASSWORD = os.environ.get("MYSQL_PWD", "在这里填你的root密码")
HOST, PORT, DB = "127.0.0.1", 3306, "olist"

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

if "填" in PASSWORD:
    sys.exit("还没填密码：先执行  $env:MYSQL_PWD=\"你的密码\"  再运行本脚本")

engine = create_engine(
    f"mysql+pymysql://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DB}?charset=utf8mb4",
    pool_pre_ping=True)
try:
    with engine.connect() as c:
        c.execute(text("SELECT 1"))
except Exception as e:
    sys.exit(f"连不上 MySQL：{e}")

DAYS = "DATEDIFF(w.delivered_ts, w.buy_ts)"
LATE = "CASE WHEN DATEDIFF(w.delivered_ts, w.estimated_ts) > 0 THEN 1 ELSE 0 END"
WHERE = "w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL"


def run(name, sql):
    df = pd.read_sql(text(sql), engine)
    df.to_csv(OUT / f"ch2_{name}.csv", index=False, encoding="utf-8-sig")
    print(f"{name:10s} {len(df):3d} 行")
    return df


run("dist", f"""
    SELECT CASE WHEN {DAYS} <= 3  THEN '0-3天'
                WHEN {DAYS} <= 7  THEN '4-7天'
                WHEN {DAYS} <= 15 THEN '8-15天'
                WHEN {DAYS} <= 30 THEN '16-30天'
                ELSE                   '30天以上' END AS bin,
           COUNT(*) AS orders
    FROM order_wide w
    WHERE {WHERE}
    GROUP BY bin
    ORDER BY MIN({DAYS})
""")

run("state", f"""
    SELECT w.customer_state AS state, COUNT(*) AS orders,
           ROUND(AVG({DAYS}),2) AS avg_days,
           ROUND(AVG({LATE})*100,2) AS late_rate
    FROM order_wide w
    WHERE {WHERE}
    GROUP BY w.customer_state
    HAVING COUNT(*) >= 500
    ORDER BY orders DESC
""")

run("monthly", f"""
    SELECT w.buy_month AS month, COUNT(*) AS orders,
           ROUND(AVG({DAYS}),2) AS avg_days,
           ROUND(AVG({LATE})*100,2) AS late_rate,
           ROUND(AVG(DATEDIFF(w.estimated_ts, w.buy_ts)),1) AS promise
    FROM order_wide w
    WHERE {WHERE} AND w.buy_month BETWEEN '2017-01' AND '2018-08'
    GROUP BY w.buy_month ORDER BY w.buy_month
""")

run("category", f"""
    SELECT t.product_category_name_english AS category,
           COUNT(*) AS items,
           ROUND(AVG({DAYS}),2) AS avg_days,
           ROUND(AVG({LATE})*100,2) AS late_rate
    FROM order_wide w
    JOIN order_items oi ON oi.order_id = w.order_id
    JOIN products    p  ON p.product_id = oi.product_id
    LEFT JOIN product_category_name_translation t
           ON t.product_category_name = p.product_category_name
    WHERE {WHERE}
    GROUP BY t.product_category_name_english
    ORDER BY items DESC LIMIT 10
""")

print("\n完成 ->", OUT)
