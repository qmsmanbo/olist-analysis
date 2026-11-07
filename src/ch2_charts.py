# -*- coding: utf-8 -*-
"""第 2 章 · 绘图：output/ch2_*.csv → 4 张图"""
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


# ---------------------------------------------------------- 图 1：分布
d = pd.read_csv(OUT / "ch2_dist.csv")
d["share"] = (d.orders / d.orders.sum() * 100).round(2)

fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=200)
colors = [GREY, GREY, NAVY, GREY, ACCENT]
ax.bar(d.bin, d.orders / 1000, color=colors, width=0.62)
tidy(ax)
ax.set_ylabel("订单数（千单）", fontsize=11, color=TEXT)
for x, (v, s) in enumerate(zip(d.orders / 1000, d.share)):
    ax.text(x, v + 0.6, f"{s:.1f}%", ha="center", fontsize=11, color=TEXT,
            fontweight="bold" if x in (2, 4) else "normal")
ax.set_ylim(0, (d.orders / 1000).max() * 1.2)
ax.set_title("近一半订单 8–15 天送达，但 4.5% 超过 30 天",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.05,
         "注：按天截断计算（DATEDIFF），样本 96,470 单，仅含已送达订单。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch2_01_dist.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch2_01_dist.png")

# ---------------------------------------------------------- 图 2：分州
s = pd.read_csv(OUT / "ch2_state.csv")
if "customer_state" in s.columns:            # 兼容两种列名
    s = s.rename(columns={"customer_state": "state"})
s = s.sort_values("avg_days")
fig, ax = plt.subplots(figsize=(9, 5.4), dpi=200)
colors = [ACCENT if v > 20 else (NAVY if v < 10 else GREY) for v in s.avg_days]
ax.barh(s.state, s.avg_days, color=colors, height=0.66)
tidy(ax, axis="x")
ax.set_xlabel("平均配送天数", fontsize=11, color=TEXT)
for y, (v, r) in enumerate(zip(s.avg_days, s.late_rate)):
    ax.text(v + 0.25, y, f"{v:.1f} 天 · 超时 {r:.1f}%", va="center", fontsize=9.5, color=TEXT)
ax.set_xlim(0, s.avg_days.max() * 1.28)
ax.set_title("圣保罗 8.7 天，帕拉 23.7 天 —— 慢是地理问题，快慢差 2.7 倍",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
fig.text(0.01, -0.04, "注：仅展示订单数 ≥ 500 的州（19 个），按平均天数升序。",
         fontsize=9, color="#777777")
plt.tight_layout()
fig.savefig(FIG / "ch2_02_state.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch2_02_state.png")

# ---------------------------------------------------------- 图 3：月度
m = pd.read_csv(OUT / "ch2_monthly.csv")
fig, ax1 = plt.subplots(figsize=(11, 4.8), dpi=200)
ax1.bar(m.month, m.avg_days, color=NAVY, width=0.62)
tidy(ax1)
ax1.set_ylabel("平均配送天数", fontsize=11, color=TEXT)
ax1.set_ylim(0, m.avg_days.max() * 1.35)

ax2 = ax1.twinx()
ax2.plot(m.month, m.late_rate, color=ACCENT, marker="o", markersize=4, linewidth=1.7)
ax2.set_ylabel("超时率（%）", fontsize=11, color=ACCENT)
ax2.tick_params(axis="y", colors=ACCENT, labelsize=9)
ax2.set_ylim(0, m.late_rate.max() * 1.25)
for sp in ("top", "left"):
    ax2.spines[sp].set_visible(False)
ax2.spines["right"].set_color(ACCENT)

peak = m.loc[m.late_rate.idxmax()]
ax2.annotate(f"超时率 {peak.late_rate:.1f}%", xy=(list(m.month).index(peak.month), peak.late_rate),
             xytext=(0, 10), textcoords="offset points", ha="center",
             fontsize=10, color=ACCENT, fontweight="bold")
ax1.set_xticks(range(len(m.month)))
ax1.set_xticklabels(m.month, rotation=45, ha="right", fontsize=9)
ax1.set_title("大促月配送恶化：2018-03 平均 16.2 天、超时率 19%，是常态的 5 倍",
              fontsize=14, fontweight="bold", color=NAVY, pad=14)
plt.tight_layout()
fig.savefig(FIG / "ch2_03_monthly.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch2_03_monthly.png")

# ---------------------------------------------------------- 图 4：承诺 vs 实际
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=200)
ax.plot(m.month, m.promise, color=GREY, linewidth=2.4, marker="s", markersize=3.5,
        label="承诺送达天数（ETA）")
ax.plot(m.month, m.avg_days, color=NAVY, linewidth=2.4, marker="o", markersize=3.5,
        label="实际送达天数")
ax.fill_between(range(len(m)), m.avg_days, m.promise, color=GREY, alpha=0.28)
tidy(ax)
ax.set_ylabel("天数", fontsize=11, color=TEXT)
ax.set_xticks(range(len(m.month)))
ax.set_xticklabels(m.month, rotation=45, ha="right", fontsize=9)
ax.legend(loc="upper left", frameon=False, fontsize=10.5)
ax.set_ylim(0, m.promise.max() * 1.2)

first, last = m.iloc[0], m.iloc[-1]
gap_first = first.promise - first.avg_days
gap_last = last.promise - last.avg_days

ax.annotate(f"{last.month}：承诺 {last.promise:.0f} 天 / 实际 {last.avg_days:.1f} 天\n"
            f"缓冲只剩 {gap_last:.1f} 天",
            xy=(len(m) - 1, last.avg_days), xytext=(-80, 105),
            textcoords="offset points", fontsize=10, color=ACCENT, ha="center",
            arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1))
ax.set_title(f"承诺从 {first.promise:.0f} 天压到 {last.promise:.0f} 天，"
             f"缓冲从 {gap_first:.0f} 天缩到 {gap_last:.0f} 天：越快反而越容易超时",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
plt.tight_layout()
fig.savefig(FIG / "ch2_04_promise.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch2_04_promise.png")
print("\n全部图 ->", FIG)
