#!/usr/bin/env python3
"""Analyze & compare gpt-oss-120b benchmark configs across TRT-LLM and vLLM backends.

Excludes agg-trtllm-native (per request). Data dirs live one level up from this
script (analysis/ -> 03062026-result/<config>/perf/...).
"""
import json, re, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))   # .../analysis
DATA = os.path.dirname(BASE)                         # .../03062026-result

# label -> (dir, backend, serving, kvmgr)
CONFIGS = [
    ("trt-agg-native",     "agg-trtllm-native-p95", "TRT-LLM", "Aggregated",    "Native"),
    ("trt-agg-kvbm",       "agg-trtllm-kvbm-p95",   "TRT-LLM", "Aggregated",    "KVBM"),
    ("trt-disagg-native",  "disagg-trtllm-native",  "TRT-LLM", "Disaggregated", "Native"),
    ("trt-disagg-kvbm",    "disagg-trtllm-kvbm",    "TRT-LLM", "Disaggregated", "KVBM"),
    ("vllm-disagg-native", "disagg-vllm-native",    "vLLM",    "Disaggregated", "Native"),
    ("vllm-disagg-kvbm",   "disagg-vllm-kvbm",      "vLLM",    "Disaggregated", "KVBM"),
]

def runtime_rps(d):
    log = open(os.path.join(DATA, d, "perf", "load_test.log")).read()
    rt  = float(re.search(r"runtime_sec = ([\d.]+)", log).group(1))
    rps = float(re.search(r"requests_per_sec = ([\d.]+)", log).group(1))
    return rt, rps

def pct(a, p): return float(np.percentile(a, p))

rows = []
for label, d, backend, serving, kv in CONFIGS:
    s = json.load(open(os.path.join(DATA, d, "perf", "multi_turn_stats.json")))
    ttft = np.array([r["ttft_ms"] for r in s])
    tpot = np.array([r["tpot_ms"] for r in s])
    lat  = np.array([r["latency_ms"] for r in s])
    out  = np.array([r["output_num_tokens"] for r in s])
    rt, rps = runtime_rps(d)
    total_out = out.sum()
    rows.append(dict(
        label=label, backend=backend, serving=serving, kv=kv, n=len(s),
        runtime=rt, rps=rps,
        out_tok_s=total_out/rt,
        ttft_mean=ttft.mean(), ttft_p50=pct(ttft,50), ttft_p95=pct(ttft,95), ttft_p99=pct(ttft,99),
        tpot_mean=tpot.mean(), tpot_p50=pct(tpot,50), tpot_p95=pct(tpot,95), tpot_p99=pct(tpot,99),
        lat_mean=lat.mean(),  lat_p50=pct(lat,50),   lat_p95=pct(lat,95),   lat_p99=pct(lat,99),
        ttft=ttft, tpot=tpot, lat=lat,
    ))

# ---- print markdown table ----
def f(x): return f"{x:,.1f}"
print("\n| Config | Backend | Serving | KV mgr | Runtime(s) | RPS | Out tok/s | TTFT p50 | TTFT p95 | TTFT p99 | TPOT mean | TPOT p95 | E2E p50 | E2E p95 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['label']} | {r['backend']} | {r['serving']} | {r['kv']} | {f(r['runtime'])} | {r['rps']:.3f} | {f(r['out_tok_s'])} "
          f"| {f(r['ttft_p50'])} | {f(r['ttft_p95'])} | {f(r['ttft_p99'])} | {r['tpot_mean']:.2f} | {r['tpot_p95']:.2f} "
          f"| {f(r['lat_p50'])} | {f(r['lat_p95'])} |")

# save table data as json for reference
json.dump([{k:v for k,v in r.items() if k not in ('ttft','tpot','lat')} for r in rows],
          open(os.path.join(BASE,"summary.json"),"w"), indent=2)

# ===================== PLOTS =====================
IMG = os.path.join(BASE, "images"); os.makedirs(IMG, exist_ok=True)
labels = [r["label"] for r in rows]
# colour by backend family: TRT-LLM = blues/greens, vLLM = oranges
colors = {
    "trt-agg-native":     "#4C72B0",
    "trt-agg-kvbm":       "#55A868",
    "trt-disagg-native":  "#C44E52",
    "trt-disagg-kvbm":    "#8172B3",
    "vllm-disagg-native": "#DD8452",
    "vllm-disagg-kvbm":   "#CCB974",
}
clist  = [colors[l] for l in labels]

plt.rcParams.update({"figure.dpi":130, "font.size":10})

def annotate(ax, bars, vals):
    for b,v in zip(bars,vals):
        ax.text(b.get_x()+b.get_width()/2, v, f"{v:,.1f}", ha='center', va='bottom', fontsize=8)

# ---- Figure 1: throughput dashboard (runtime, rps, out tok/s) ----
fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
metrics = [("runtime","Total runtime (s) — lower is better"),
           ("rps","Requests / sec — higher is better"),
           ("out_tok_s","Output tokens / sec — higher is better")]
for ax,(key,title) in zip(axes, metrics):
    vals=[r[key] for r in rows]
    bars=ax.bar(labels, vals, color=clist)
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis='x', rotation=30)
    annotate(ax, bars, vals)
    ax.margins(y=0.15)
fig.suptitle("gpt-oss-120b — Throughput & system-level metrics (TRT-LLM vs vLLM)", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(IMG,"plot_throughput.png"), bbox_inches='tight')

# ---- Figure 2: latency percentile grouped bars (TTFT, TPOT, E2E) ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))
x = np.arange(len(labels)); w=0.25
pgroups=[("ttft","TTFT (ms) — lower is better"),
         ("tpot","TPOT (ms/token) — lower is better"),
         ("lat","End-to-end latency (ms) — lower is better")]
for ax,(pre,title) in zip(axes,pgroups):
    for i,p in enumerate(["p50","p95","p99"]):
        vals=[r[f"{pre}_{p}"] for r in rows]
        ax.bar(x+(i-1)*w, vals, w, label=p.upper())
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha='right')
    ax.set_title(title, fontsize=11); ax.legend(fontsize=8)
fig.suptitle("gpt-oss-120b — Latency percentiles (p50 / p95 / p99)", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(IMG,"plot_latency_percentiles.png"), bbox_inches='tight')

# ---- Figure 3: TTFT & TPOT distribution (CDF) ----
fig, (ax1,ax2)=plt.subplots(1,2,figsize=(15,5.5))
for r in rows:
    d=np.sort(r["ttft"]); cdf=np.arange(1,len(d)+1)/len(d)
    ax1.plot(d/1000, cdf, label=r["label"], color=colors[r["label"]], lw=2)
ax1.set_xlabel("TTFT (s)"); ax1.set_ylabel("Cumulative fraction of requests")
ax1.set_title("TTFT CDF — leftmost curve is best"); ax1.legend(fontsize=8); ax1.grid(alpha=.3)
ax1.axhline(0.95, ls='--', c='gray', lw=.8); ax1.text(ax1.get_xlim()[1]*.6,0.955,"p95",color='gray',fontsize=8)

for r in rows:
    d=np.sort(r["tpot"]); cdf=np.arange(1,len(d)+1)/len(d)
    ax2.plot(d, cdf, label=r["label"], color=colors[r["label"]], lw=2)
ax2.set_xlabel("TPOT (ms/token)"); ax2.set_ylabel("Cumulative fraction of requests")
ax2.set_title("TPOT CDF — leftmost curve is best"); ax2.legend(fontsize=8); ax2.grid(alpha=.3)
fig.suptitle("gpt-oss-120b — Per-request latency distributions", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(IMG,"plot_distributions.png"), bbox_inches='tight')

# ---- Figure 4: throughput vs latency trade-off (Pareto scatter) ----
fig, ax = plt.subplots(figsize=(8.5, 6))
for r in rows:
    ax.scatter(r["out_tok_s"], r["lat_p95"]/1000, s=140, color=colors[r["label"]],
               edgecolor='black', zorder=3)
    ax.annotate(r["label"], (r["out_tok_s"], r["lat_p95"]/1000),
                textcoords="offset points", xytext=(8,5), fontsize=9)
ax.set_xlabel("Throughput — output tokens / sec (higher is better →)")
ax.set_ylabel("E2E latency p95 (s) — lower is better ↓")
ax.set_title("Throughput vs tail-latency trade-off\n(bottom-right = best)", fontsize=12, fontweight='bold')
ax.grid(alpha=.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG,"plot_tradeoff.png"), bbox_inches='tight')

print("\nSaved images/: plot_throughput.png, plot_latency_percentiles.png, plot_distributions.png, plot_tradeoff.png + summary.json")
