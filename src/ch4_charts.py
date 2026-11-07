# -*- coding: utf-8 -*-
"""第 4 章 · 绘图：cohort 复购率 / 体验 × 复购"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
NAVY, ACCENT, GREY, TEXT = "#1B3358", "#C0504D", "#C9D3E0", "#333333"

BASE = Path(__file__).resolve().parent.parent
OUT, FIG = BASE / "output", BASE / "output" / "figs"


def tidy(ax, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#AAAAAA")
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.grid(axis=axis, color="#EEEEEE", linewidth=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------- 图 1：cohort
c = pd.read_csv(OUT / "ch4_cohort.csv")
c = c[c.customers >= 300]
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=200)
colors = [NAVY if m <= "2017-12" else ACCENT for m in c.month]
ax.bar(c.month, c.rate, color=colors, width=0.66)
tidy(ax)
ax.set_ylabel("12 个月后的复购率（%）", fontsize=11, color=TEXT)
ax.axhline(3.12, color="#888888", linestyle="--", linewidth=1.2, zorder=1)

for x, (m, v) in enumerate(zip(c.month, c.rate)):
    if m in ("2017-01", "2017-05", "2018-08"):
        ax.text(x, v + 0.15, f"{v:.1f}%", ha="center", fontsize=10, color=TEXT, fontweight="bold")

ax.set_xticks(range(len(c.month)))
ax.set_xticklabels(c.month, rotation=45, ha="right", fontsize=9)
ax.set_ylim(0, 8.6)
ax.axvspan(len(c) - 5, len(c) - 0.4, color=ACCENT, alpha=0.08, zorder=0)
ax.text(len(c) - 2.6, 7.3, "观察期不足半年\n复购率被系统性低估", ha="center",
        fontsize=10, color=ACCENT, linespacing=1.4)
ax.set_title("按首购月份看：2017 年 cohort 有 4.6–5.5%，2018 年下半年只剩 1%",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.05,
         "注：样本为首购客户数 ≥ 300 的月份；复购 = 客户名下订单数 ≥ 2；虚线为整体复购率 3.12%。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch4_01_cohort.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch4_01_cohort.png")

# ---------------------------------------------------- 图 2：体验 × 复购
q = pd.read_csv(OUT / "ch4_quad.csv")
q[["lat", "ev"]] = q.组.str.split("·", expand=True)
pivot = q.pivot(index="ev", columns="lat", values="rate").loc[["好评", "中评", "差评"]]

fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=200)
x = range(len(pivot))
w = 0.34
b1 = ax.bar([i - w / 2 for i in x], pivot["准时"], width=w, color=NAVY, label="首单准时")
b2 = ax.bar([i + w / 2 for i in x], pivot["超时"], width=w, color=ACCENT, label="首单超时")
tidy(ax)
ax.set_xticks(list(x))
ax.set_xticklabels([f"首单{ev}" for ev in pivot.index], fontsize=11.5)
ax.set_ylabel("复购率（%）", fontsize=11, color=TEXT)
ax.set_ylim(0, 4.8)
for bars in (b1, b2):
    for r in bars:
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.06,
                f"{r.get_height():.2f}%", ha="center", fontsize=10.5, color=TEXT)
ax.legend(loc="upper right", frameon=False, fontsize=10.5, ncol=2)
ax.set_title("首单「超时 + 差评」的客户，复购率只有准时好评客户的 2/3",
             fontsize=13.5, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.04,
         "注：样本 71,186 名首购于 2018-04 前的客户；两组差异均通过卡方检验（p < 0.001）。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch4_02_quad.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch4_02_quad.png")
