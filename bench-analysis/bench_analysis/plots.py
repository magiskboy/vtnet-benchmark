from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DEFAULT_COLORS = [
    "#4C72B0",
    "#55A868",
    "#C44E52",
    "#8172B3",
    "#DD8452",
    "#CCB974",
    "#64B5CD",
    "#DA8BC3",
]


def _resolve_colors(rows: list[dict], colors: dict[str, str] | None) -> dict[str, str]:
    if colors:
        return colors
    return {r["label"]: DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i, r in enumerate(rows)}


def _annotate_bars(ax, bars, vals):
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val,
            f"{val:,.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def save_plots(rows: list[dict], output_dir: str, title: str, colors: dict[str, str] | None = None) -> list[str]:
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    palette = _resolve_colors(rows, colors)
    labels = [r["label"] for r in rows]
    clist = [palette[l] for l in labels]

    plt.rcParams.update({"figure.dpi": 130, "font.size": 10})

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
    metrics = [
        ("runtime", "Total runtime (s) — lower is better"),
        ("rps", "Requests / sec — higher is better"),
        ("out_tok_s", "Output tokens / sec — higher is better"),
    ]
    for ax, (key, plot_title) in zip(axes, metrics):
        vals = [r[key] for r in rows]
        bars = ax.bar(labels, vals, color=clist)
        ax.set_title(plot_title, fontsize=11)
        ax.tick_params(axis="x", rotation=30)
        _annotate_bars(ax, bars, vals)
        ax.margins(y=0.15)
    fig.suptitle(f"{title} — Throughput & system-level metrics", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    throughput_path = os.path.join(img_dir, "plot_throughput.png")
    fig.savefig(throughput_path, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))
    x = np.arange(len(labels))
    w = 0.25
    pgroups = [
        ("ttft", "TTFT (ms) — lower is better"),
        ("tpot", "TPOT (ms/token) — lower is better"),
        ("lat", "End-to-end latency (ms) — lower is better"),
    ]
    for ax, (pre, plot_title) in zip(axes, pgroups):
        for i, p in enumerate(["p50", "p95", "p99"]):
            vals = [r[f"{pre}_{p}"] for r in rows]
            ax.bar(x + (i - 1) * w, vals, w, label=p.upper())
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_title(plot_title, fontsize=11)
        ax.legend(fontsize=8)
    fig.suptitle(f"{title} — Latency percentiles (p50 / p95 / p99)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    latency_path = os.path.join(img_dir, "plot_latency_percentiles.png")
    fig.savefig(latency_path, bbox_inches="tight")
    plt.close(fig)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
    for r in rows:
        d = np.sort(r["ttft"])
        cdf = np.arange(1, len(d) + 1) / len(d)
        ax1.plot(d / 1000, cdf, label=r["label"], color=palette[r["label"]], lw=2)
    ax1.set_xlabel("TTFT (s)")
    ax1.set_ylabel("Cumulative fraction of requests")
    ax1.set_title("TTFT CDF — leftmost curve is best")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)
    ax1.axhline(0.95, ls="--", c="gray", lw=0.8)
    ax1.text(ax1.get_xlim()[1] * 0.6, 0.955, "p95", color="gray", fontsize=8)

    for r in rows:
        d = np.sort(r["tpot"])
        cdf = np.arange(1, len(d) + 1) / len(d)
        ax2.plot(d, cdf, label=r["label"], color=palette[r["label"]], lw=2)
    ax2.set_xlabel("TPOT (ms/token)")
    ax2.set_ylabel("Cumulative fraction of requests")
    ax2.set_title("TPOT CDF — leftmost curve is best")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    fig.suptitle(f"{title} — Per-request latency distributions", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    dist_path = os.path.join(img_dir, "plot_distributions.png")
    fig.savefig(dist_path, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 6))
    for r in rows:
        ax.scatter(
            r["out_tok_s"],
            r["lat_p95"] / 1000,
            s=140,
            color=palette[r["label"]],
            edgecolor="black",
            zorder=3,
        )
        ax.annotate(
            r["label"],
            (r["out_tok_s"], r["lat_p95"] / 1000),
            textcoords="offset points",
            xytext=(8, 5),
            fontsize=9,
        )
    ax.set_xlabel("Throughput — output tokens / sec (higher is better →)")
    ax.set_ylabel("E2E latency p95 (s) — lower is better ↓")
    ax.set_title(
        "Throughput vs tail-latency trade-off\n(bottom-right = best)",
        fontsize=12,
        fontweight="bold",
    )
    ax.grid(alpha=0.3)
    fig.tight_layout()
    tradeoff_path = os.path.join(img_dir, "plot_tradeoff.png")
    fig.savefig(tradeoff_path, bbox_inches="tight")
    plt.close(fig)

    return [throughput_path, latency_path, dist_path, tradeoff_path]
