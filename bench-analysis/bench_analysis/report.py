import json
import os


def _fmt(x: float) -> str:
    return f"{x:,.1f}"


def print_markdown_table(rows: list[dict]) -> None:
    print(
        "\n| Config | Backend | Serving | KV mgr | Runtime(s) | RPS | Out tok/s | "
        "TTFT p50 | TTFT p95 | TTFT p99 | TPOT mean | TPOT p95 | E2E p50 | E2E p95 |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| {r['label']} | {r['backend']} | {r['serving']} | {r['kv']} | "
            f"{_fmt(r['runtime'])} | {r['rps']:.3f} | {_fmt(r['out_tok_s'])} "
            f"| {_fmt(r['ttft_p50'])} | {_fmt(r['ttft_p95'])} | {_fmt(r['ttft_p99'])} | "
            f"{r['tpot_mean']:.2f} | {r['tpot_p95']:.2f} "
            f"| {_fmt(r['lat_p50'])} | {_fmt(r['lat_p95'])} |"
        )


def save_summary(rows: list[dict], output_dir: str) -> str:
    path = os.path.join(output_dir, "summary.json")
    with open(path, "w") as f:
        json.dump(
            [{k: v for k, v in r.items() if k not in ("ttft", "tpot", "lat")} for r in rows],
            f,
            indent=2,
        )
    return path
