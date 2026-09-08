"""Generates docs/model_performance.png -- the ndcg@10 comparison chart in the README's
"Results, honestly" section.

Numbers are the same train+val (n=15) figures used to actually choose between configurations
(experiments/experiment_register.md: EXP10, EXP30, EXP14, EXP32, EXP33, EXP34) -- not the
held-out test-split number, which is a different (and much smaller, n=3) measurement shown
separately in the README text rather than mixed into this chart.

Run: python evaluation/plot_model_comparison.py
Requires matplotlib (not a project dependency elsewhere -- this is the one place it's used).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "model_performance.png"

LABELS = [
    "PostgreSQL\nfull-text",
    "Vector-only\n(semantic)",
    "BM25\n(tuned)",
    "RRF\nfusion",
    "Equal-weight\nfusion",
    "Weighted fusion\n90/10 (LIVE)",
]
SCORES = [0.355, 0.293, 0.755, 0.549, 0.673, 0.765]
BM25_BASELINE = 0.755  # the bar hybrid fusion actually had to beat
CHOSEN_INDEX = 5

# gray = baseline, red/orange = rejected fusion attempt, green = chosen/live
COLORS = ["#9ca3af", "#9ca3af", "#6b7280", "#f87171", "#fb923c", "#22c55e"]


def build_chart() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(LABELS, SCORES, color=COLORS, edgecolor="white", linewidth=0.5, width=0.62)

    ax.axhline(BM25_BASELINE, color="#374151", linestyle="--", linewidth=1, alpha=0.6)
    ax.text(-0.45, BM25_BASELINE + 0.02, "BM25 baseline to beat", fontsize=8.5, color="#374151", ha="left")

    for bar, score in zip(bars, SCORES, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            score + 0.018,
            f"{score:.3f}",
            ha="center",
            fontsize=9.5,
            fontweight="bold",
            color="#111827",
        )

    bars[CHOSEN_INDEX].set_edgecolor("#15803d")
    bars[CHOSEN_INDEX].set_linewidth(2.2)
    ax.annotate(
        "Chosen for\nproduction",
        xy=(CHOSEN_INDEX - 0.31, SCORES[CHOSEN_INDEX] - 0.06),
        xytext=(CHOSEN_INDEX - 1.4, 0.9),
        fontsize=10,
        fontweight="bold",
        color="#15803d",
        arrowprops={"arrowstyle": "->", "color": "#15803d", "lw": 1.6},
    )

    ax.set_ylabel("ndcg@10 (train+val, n=15)", fontsize=10)
    ax.set_ylim(0, 0.98)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_title("StyleSeek search configurations compared", fontsize=13, fontweight="bold", pad=14)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=160)


if __name__ == "__main__":
    build_chart()
    print(f"Saved {OUTPUT_PATH}")
