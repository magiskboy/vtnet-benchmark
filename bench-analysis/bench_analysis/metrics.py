from __future__ import annotations

import numpy as np

from .loader import load_multi_turn_stats, load_runtime_rps


def percentile(values: np.ndarray, p: float) -> float:
    return float(np.percentile(values, p))


def analyze_configs(project_root: str, configs: list[dict]) -> list[dict]:
    """Build per-config metric rows from benchmark result directories."""
    rows = []
    for cfg in configs:
        label = cfg["label"]
        config_dir = cfg["dir"]
        stats = load_multi_turn_stats(project_root, config_dir)
        ttft = np.array([r["ttft_ms"] for r in stats])
        tpot = np.array([r["tpot_ms"] for r in stats])
        lat = np.array([r["latency_ms"] for r in stats])
        out = np.array([r["output_num_tokens"] for r in stats])
        runtime, rps = load_runtime_rps(project_root, config_dir)
        total_out = out.sum()
        rows.append(
            {
                "label": label,
                "backend": cfg.get("backend", ""),
                "serving": cfg.get("serving", ""),
                "kv": cfg.get("kv", ""),
                "n": len(stats),
                "runtime": runtime,
                "rps": rps,
                "out_tok_s": total_out / runtime,
                "ttft_mean": float(ttft.mean()),
                "ttft_p50": percentile(ttft, 50),
                "ttft_p95": percentile(ttft, 95),
                "ttft_p99": percentile(ttft, 99),
                "tpot_mean": float(tpot.mean()),
                "tpot_p50": percentile(tpot, 50),
                "tpot_p95": percentile(tpot, 95),
                "tpot_p99": percentile(tpot, 99),
                "lat_mean": float(lat.mean()),
                "lat_p50": percentile(lat, 50),
                "lat_p95": percentile(lat, 95),
                "lat_p99": percentile(lat, 99),
                "ttft": ttft,
                "tpot": tpot,
                "lat": lat,
            }
        )
    return rows
