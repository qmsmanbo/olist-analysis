# -*- coding: utf-8 -*-
"""第 3 章 · 取数：MySQL → output/ch3_*.csv"""
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

if "填" in PASSWORD:
    sys.exit("还没填密码：先执行  set MYSQL_PWD=你的密码  （CMD）或 $env:MYSQL_PWD=\"...\"（PowerShell）")

engine = create_engine(
    f"mysql+pymysql://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DB}?charset=utf8mb4",
    pool_pre_ping=True)

CORE = """
    SELECT w.order_id,
           w.customer_state,
           DATEDIFF(w.delivered_ts, w.estimated_ts) AS late,
           AVG(r.review_score)                     AS score
    FROM order_wide w
    JOIN order_reviews r ON r.order_id = w.order_id
    WHERE w.order_status = 'delivered' AND w.delivered_ts IS NOT NULL
    GROUP BY w.order_id, w.customer_state, late
"""


def run(name, sql):
    df = pd.read_sql(text(sql), engine)
    df.to_csv(OUT / f"ch3_{name}.csv", index=False, encoding="utf-8-sig")
    print(f"{name:10s} {len(df):3d} 行")
    return df


run("late_bins", f"""
    SELECT CASE WHEN late <= 0  THEN '准时或提前'
                WHEN late <= 3  THEN '超1-3天'
                WHEN late <= 7  THEN '超4-7天'
                WHEN late <= 15 THEN '超8-15天'
                ELSE                 '超15天以上' END AS bucket,
           COUNT(*) AS orders,
           ROUND(AVG(score), 3) AS avg_score,
           ROUND(AVG(score <= 2) * 100, 2) AS bad_rate,
           ROUND(AVG(score = 1)  * 100, 2) AS one_star
    FROM ({CORE}) t GROUP BY bucket ORDER BY bucket
""")

run("attrib", f"""
    SELECT CASE WHEN score <= 2 THEN '差评(1-2星)'
                WHEN score >= 4 THEN '好评(4-5星)'
                ELSE                 '中评(3星)' END AS kind,
           COUNT(*) AS orders,
           SUM(late > 0) AS late_n,
           ROUND(SUM(late > 0) * 100.0 / COUNT(*), 2) AS late_share
    FROM ({CORE}) t GROUP BY kind ORDER BY kind
""")

run("state", f"""
    SELECT customer_state AS customer_state,
           COUNT(*) AS orders,
           ROUND(AVG(CASE WHEN late <= 0 THEN score END), 2) AS on_time,
           ROUND(AVG(CASE WHEN late >  0 THEN score END), 2) AS late_score
    FROM ({CORE}) t
    GROUP BY customer_state
    HAVING COUNT(*) >= 500
    ORDER BY orders DESC
""")

print("\n完成 ->", OUT)
