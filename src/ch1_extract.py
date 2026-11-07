# -*- coding: utf-8 -*-
"""导出第 1 章分析结果到 output/ch1_*.csv。

依赖: pymysql, sqlalchemy, pandas
数据库密码通过环境变量 MYSQL_PWD 传入。
"""
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

USER = "root"
PASSWORD = os.environ.get("MYSQL_PWD", "在这里填你的root密码")
HOST = "127.0.0.1"
PORT = 3306
DB = "olist"

BASE = Path(__file__).resolve().parent.parent          # 05_项目/olist
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

if "填" in PASSWORD:
    sys.exit("还没填密码：要么改本文件的 PASSWORD 变量，要么先设置环境变量 MYSQL_PWD")

# 密码里可能有 @ : / 等字符，必须 URL 编码，否则连接串会解析错
engine = create_engine(
    f"mysql+pymysql://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DB}?charset=utf8mb4",
    pool_pre_ping=True)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    sys.exit(f"连不上 MySQL：{e}\\n检查：服务是否启动、密码是否正确、库 olist 是否存在")

WINDOW = "w.order_status = 'delivered' AND w.buy_month BETWEEN '2017-01' AND '2018-08'"


def run(name, sql, params=None):
    df = pd.read_sql(text(sql), engine, params=params)
    path = OUT / f"ch1_{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"{name:10s} {len(df):3d} 行 -> {path.name}")
    return df


# 1.0 规模
run("overview", """
    SELECT COUNT(*) AS orders,
           ROUND(SUM(gmv),2) AS gmv,
           ROUND(SUM(freight),2) AS freight,
           ROUND(SUM(gmv)/COUNT(*),2) AS aov,
           ROUND((SUM(gmv)+SUM(freight))/COUNT(*),2) AS aov_with_freight
    FROM order_wide WHERE order_status='delivered'
""")

# 1.1 月度
run("monthly", f"""
    SELECT w.buy_month AS month, COUNT(*) AS orders,
           ROUND(SUM(w.gmv),2) AS gmv,
           ROUND(SUM(w.gmv)/COUNT(*),2) AS aov
    FROM order_wide w
    WHERE {WINDOW}
    GROUP BY w.buy_month ORDER BY w.buy_month
""")

# 1.2 州
run("state", f"""
    SELECT w.customer_state AS state, COUNT(*) AS orders,
           ROUND(SUM(w.gmv),2) AS gmv,
           ROUND(SUM(w.gmv)*100.0/SUM(SUM(w.gmv)) OVER (),2) AS share
    FROM order_wide w
    WHERE {WINDOW}
    GROUP BY w.customer_state ORDER BY gmv DESC LIMIT 10
""")

# 1.3 品类
run("category", f"""
    SELECT t.product_category_name_english AS category,
           COUNT(DISTINCT w.order_id) AS orders,
           ROUND(SUM(oi.price),2) AS gmv,
           ROUND(SUM(oi.price)*100.0/SUM(SUM(oi.price)) OVER (),2) AS share
    FROM order_wide w
    JOIN order_items oi ON oi.order_id = w.order_id
    JOIN products p ON p.product_id = oi.product_id
    LEFT JOIN product_category_name_translation t
           ON t.product_category_name = p.product_category_name
    WHERE {WINDOW}
    GROUP BY t.product_category_name_english
    ORDER BY gmv DESC LIMIT 10
""")

# 1.4 支付
run("payment", f"""
    SELECT p.payment_type AS payment_type,
           COUNT(DISTINCT p.order_id) AS orders,
           ROUND(SUM(p.payment_value),2) AS amount,
           ROUND(SUM(p.payment_value)*100.0/SUM(SUM(p.payment_value)) OVER (),2) AS share
    FROM order_payments p
    JOIN order_wide w ON w.order_id = p.order_id
    WHERE {WINDOW}
    GROUP BY p.payment_type ORDER BY amount DESC
""")

print("\n全部结果已写入", OUT)
