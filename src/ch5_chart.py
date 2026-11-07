# -*- coding: utf-8 -*-
"""第 5 章 · 因果链示意图"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
NAVY, ACCENT, GREY, TEXT = "#1B3358", "#C0504D", "#C9D3E0", "#333333"

FIG = Path(__file__).resolve().parent.parent / "output" / "figs"
FIG.mkdir(parents=True, exist_ok=True)

STAGES = [
    ("大促集中\n（2017-11 / 2018-03）", "订单量冲到月均 1.5 倍", NAVY),
    ("物流被挤压\n超时率飙升", "12.4% → 19.0%\n（常态 3%）", ACCENT),
    ("评分断崖\n差评率 68%", "4.29 分 → 2.11 分\n超时 >4 天", ACCENT),
    ("客户不再回来\n复购率 2.52%", "准时好评组 3.82%", ACCENT),
    ("增长靠拉新\n无法复利", "GMV 冲高后横盘", NAVY),
]

fig, ax = plt.subplots(figsize=(13, 4.2), dpi=200)
ax.set_xlim(0, 13)
ax.set_ylim(0, 4.2)
ax.axis("off")

w, h, gap = 2.15, 1.5, 0.42
x = 0.28
centers = []
for i, (title, sub, color) in enumerate(STAGES):
    box = FancyBboxPatch((x, 1.75), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                         linewidth=1.4, edgecolor=color, facecolor="#FFFFFF", zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, 1.75 + h - 0.32, title, ha="center", va="center",
            fontsize=11.5, color=color, fontweight="bold", linespacing=1.35, zorder=3)
    ax.text(x + w / 2, 1.75 + 0.42, sub, ha="center", va="center",
            fontsize=9.8, color=TEXT, linespacing=1.35, zorder=3)
    centers.append(x + w / 2)
    if i < len(STAGES) - 1:
        arr = FancyArrowPatch((x + w + 0.05, 2.5), (x + w + gap - 0.05, 2.5),
                              arrowstyle="-|>", mutation_scale=16,
                              linewidth=1.6, color="#9AA5B4", zorder=1)
        ax.add_patch(arr)
    x += w + gap

# 底部：只做一件事
ax.text(0.3, 1.05, "如果只能做一件事：", fontsize=11.5, color=NAVY, fontweight="bold")
ax.text(0.3, 0.62,
        "把大促期间的 ETA 从 22.7 天放宽到 26 天 —— 零成本、立刻见效，"
        "超时率可从 19% 压到常态 3%，减少约 1,100 单超时",
        fontsize=10.5, color=TEXT)
ax.text(0.3, 0.22,
        "风险：承诺变长可能压低下单转化，需用 A/B 测试验证（两周即可出结论）",
        fontsize=10, color="#777777")

ax.set_title("因果链：一次大促的履约崩塌，如何影响两年后的增长",
             fontsize=15, fontweight="bold", color=NAVY, pad=10)
plt.tight_layout()
fig.savefig(FIG / "ch5_01_chain.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved ch5_01_chain.png ->", FIG)
