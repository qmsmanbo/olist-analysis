# -*- coding: utf-8 -*-
"""读取 output/ch1_*.csv，生成第 1 章的三张图。

图题采用结论式表述；统一去掉上右边框，强调色只用于需要突出的数据点。
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#1B3358"
ACCENT = "#C0504D"
GREY = "#C9D3E0"
TEXT = "#333333"

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output"
FIG = OUT / "figs"
FIG.mkdir(parents=True, exist_ok=True)


def tidy(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#AAAAAA")
    ax.spines["bottom"].set_color("#AAAAAA")
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.grid(axis=grid_axis, color="#EEEEEE", linewidth=0.8)
    ax.set_axisbelow(True)


# ============================================================ 图 1：月度
m = pd.read_csv(OUT / "ch1_monthly.csv")
m["gmv_wan"] = m["gmv"] / 10000

fig, ax1 = plt.subplots(figsize=(11, 5.2), dpi=200)
colors = [ACCENT if x == "2017-11" else NAVY for x in m["month"]]
bars = ax1.bar(m["month"], m["gmv_wan"], color=colors, width=0.68)

ax1.set_ylabel("GMV（万元）", fontsize=11, color=TEXT)
ax1.set_ylim(0, m["gmv_wan"].max() * 1.22)
tidy(ax1)

ax2 = ax1.twinx()
ax2.plot(m["month"], m["aov"], color=ACCENT, marker="o", markersize=4,
         linewidth=1.6, label="AOV（元）")
ax2.set_ylabel("AOV（元）", fontsize=11, color=ACCENT)
ax2.tick_params(axis="y", colors=ACCENT, labelsize=9)
ax2.set_ylim(100, 165)
for side in ("top", "left"):
    ax2.spines[side].set_visible(False)
ax2.spines["right"].set_color(ACCENT)

# 只标注峰值
peak = m.loc[m["gmv_wan"].idxmax()]
ax1.annotate(f"{peak['gmv_wan']:.1f} 万\n黑五 · 月均的 1.5 倍",
             xy=(list(m["month"]).index(peak["month"]), peak["gmv_wan"]),
             xytext=(0, 14), textcoords="offset points",
             ha="center", fontsize=10, color=ACCENT, fontweight="bold")

ax1.set_title("GMV 20 个月增长 7.5 倍，2017-11 黑五冲高后进入 80–98 万平台期",
              fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax1.set_xticks(range(len(m['month'])))
ax1.set_xticklabels(m['month'], rotation=45, ha='right', fontsize=9.5)
ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}"))
plt.tight_layout()
fig.savefig(FIG / "ch1_01_monthly_gmv.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch1_01_monthly_gmv.png")


# ============================================================ 图 2：州
s = pd.read_csv(OUT / "ch1_state.csv").sort_values("gmv")
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
colors = [NAVY if x == "SP" else GREY for x in s["state"]]
ax.barh(s["state"], s["gmv"] / 10000, color=colors, height=0.66)
tidy(ax, grid_axis="x")
ax.set_xlabel("GMV（万元）", fontsize=11, color=TEXT)

for y, (v, sh) in enumerate(zip(s["gmv"] / 10000, s["share"])):
    ax.text(v + 3, y, f"{sh:.1f}%", va="center", fontsize=10,
            color=NAVY if s["state"].iloc[y] == "SP" else TEXT,
            fontweight="bold" if s["state"].iloc[y] == "SP" else "normal")

ax.set_title("圣保罗一州占 38.4%，前三州合计 63.4%",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_xlim(0, (s["gmv"] / 10000).max() * 1.15)
plt.tight_layout()
fig.savefig(FIG / "ch1_02_state.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch1_02_state.png")


# ============================================================ 图 3：品类
c = pd.read_csv(OUT / "ch1_category.csv").sort_values("gmv")
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
colors = [NAVY if i == len(c) - 1 else GREY for i in range(len(c))]
ax.barh(c["category"], c["gmv"] / 10000, color=colors, height=0.66)
tidy(ax, grid_axis="x")
ax.set_xlabel("GMV（万元）", fontsize=11, color=TEXT)

for y, (v, sh) in enumerate(zip(c["gmv"] / 10000, c["share"])):
    ax.text(v + 0.8, y, f"{sh:.2f}%", va="center", fontsize=10,
            color=TEXT, fontweight="bold" if y == len(c) - 1 else "normal")

ax.set_xlim(0, (c["gmv"] / 10000).max() * 1.18)
ax.set_title("品类高度分散：第一名仅 9.3%，Top10 合计 62.5%",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.06,
         "注：占比分母为全部 GMV，含 595 个未标注品类的商品（占 1.33%），故各品类合计不足 100%。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch1_03_category.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch1_03_category.png")
print("\n图都在这儿：", FIG)
