# -*- coding: utf-8 -*-
"""第 3 章 · 绘图：断崖曲线 / 差评归因 / 分州哑铃图"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY, ACCENT, GREY, TEXT = "#1B3358", "#C0504D", "#C9D3E0", "#333333"
BASE = Path(__file__).resolve().parent.parent
OUT, FIG = BASE / "output", BASE / "output" / "figs"
FIG.mkdir(parents=True, exist_ok=True)


def tidy(ax, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#AAAAAA")
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.grid(axis=axis, color="#EEEEEE", linewidth=0.8)
    ax.set_axisbelow(True)


# ==================================================== 图 1：断崖
g = pd.read_csv(OUT / "ch3_late_bins.csv")
fig, ax1 = plt.subplots(figsize=(10, 5.2), dpi=200)

colors = [NAVY] + [ACCENT] * 4
bars = ax1.bar(g.bucket, g.avg_score, color=colors, width=0.6)
tidy(ax1)
ax1.set_ylabel("平均评分（1-5 星）", fontsize=11, color=TEXT)
ax1.set_ylim(0, 5.6)
for x, v in enumerate(g.avg_score):
    ax1.text(x, v + 0.12, f"{v:.2f}", ha="center", fontsize=11.5,
             color=TEXT, fontweight="bold")

ax2 = ax1.twinx()
ax2.plot(g.bucket, g.bad_rate, color="#7A2E2C", marker="o", markersize=6,
         linewidth=1.8, zorder=5)
ax2.set_ylabel("差评率（1-2 星，%）", fontsize=11, color="#7A2E2C")
ax2.tick_params(axis="y", colors="#7A2E2C", labelsize=9)
ax2.set_ylim(0, 100)
for sp in ("top", "left"):
    ax2.spines[sp].set_visible(False)
ax2.spines["right"].set_color("#7A2E2C")
for x, v in enumerate(g.bad_rate):
    ax2.annotate(f"{v:.0f}%", xy=(x, v), xytext=(0, 11), textcoords="offset points",
                 ha="center", fontsize=10, color="#7A2E2C", fontweight="bold",
                 bbox=dict(facecolor="white", edgecolor="none", pad=1.2))

ax1.axvspan(3.5, 4.5, color=GREY, alpha=0.22, zorder=0)
ax1.text(4, 3.15, "超 8 天后评分见底\n再晚也不会更差", ha="center", fontsize=10,
         color=NAVY, linespacing=1.4)
ax1.set_title("一超时就掉 1 分：评分是断崖式下跌，不是慢慢变差",
              fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.04,
         "样本 95,824 单（已送达且有评价）；平均分见柱体，差评率见折线。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch3_01_cliff.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch3_01_cliff.png")

# ==================================================== 图 2：差评归因
a = pd.read_csv(OUT / "ch3_attrib.csv")
order = ["好评(4-5星)", "中评(3星)", "差评(1-2星)"]
a = a.set_index("kind").loc[order].reset_index()
a["on_time_share"] = 100 - a.late_share

fig, ax = plt.subplots(figsize=(10, 3.6), dpi=200)
y = range(len(a))
ax.barh(y, a.on_time_share, color=GREY, height=0.55, label="准时送达")
ax.barh(y, a.late_share, left=a.on_time_share, color=ACCENT, height=0.55, label="超时送达")
ax.set_yticks(list(y))
ax.set_yticklabels(a.kind, fontsize=11.5)
ax.set_xlim(0, 100)
ax.set_xlabel("占比（%）", fontsize=11, color=TEXT)
tidy(ax, axis="x")
for i, row in a.iterrows():
    ax.text(row.on_time_share - 1.5, i, f"准时 {row.on_time_share:.1f}%",
            ha="right", va="center", fontsize=10, color=TEXT)
    ax.text(101, i, f"超时 {row.late_share:.1f}%  ({int(row.late_n):,} 单)",
            ha="left", va="center", fontsize=10, color=ACCENT, fontweight="bold")
ax.legend(loc="lower left", bbox_to_anchor=(0, -0.42), ncol=2, frameon=False, fontsize=10)
ax.set_title("超时订单只占 6.7%，却贡献了 32.5% 的差评",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
plt.tight_layout()
fig.savefig(FIG / "ch3_02_attrib.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch3_02_attrib.png")

# ==================================================== 图 3：分州哑铃
s = pd.read_csv(OUT / "ch3_state.csv").sort_values("on_time", ascending=True).tail(12)
fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
ys = range(len(s))
ax.hlines(ys, s.late_score, s.on_time, color="#D9D9D9", linewidth=4, zorder=1)
ax.scatter(s.late_score, ys, s=95, color=ACCENT, zorder=3, label="超时订单")
ax.scatter(s.on_time, ys, s=95, color=NAVY, zorder=3, label="准时订单")
ax.set_yticks(list(ys))
ax.set_yticklabels(s.customer_state, fontsize=11)
ax.set_xlim(1.2, 4.9)
ax.set_xlabel("平均评分（1-5 星）", fontsize=11, color=TEXT)
tidy(ax, axis="x")

for i, row in enumerate(s.itertuples()):
    ax.text(row.on_time + 0.08, i, f"{row.on_time:.2f}", va="center", fontsize=9.5, color=NAVY)
    ax.text(row.late_score - 0.08, i, f"{row.late_score:.2f}", va="center",
            ha="right", fontsize=9.5, color=ACCENT)

ax.legend(loc="upper left", frameon=False, fontsize=10, ncol=2, bbox_to_anchor=(0.0, 1.02))
ax.set_title("每个州都掉 1.7–2.4 分：不是「偏远州用户更挑剔」",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.03,
         "注：仅展示订单数 ≥ 500 且准时组评分最高的 12 个州；左端为超时组、右端为准时组。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch3_03_state.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch3_03_state.png")
print("\n全部图 ->", FIG)
