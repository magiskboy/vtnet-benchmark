#!/usr/bin/env python3
"""Analyze & compare gpt-oss-120b TRT-LLM benchmark configs (excl. agg-trtllm-native)."""
import json, re, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))

# label -> (dir, serving, kvmgr)
CONFIGS = [
    ("agg-native",    "agg-trtllm-native-p95", "Aggregated",    "Native"),
    ("agg-kvbm",      "agg-trtllm-kvbm-p95",   "Aggregated",    "KVBM"),
    ("disagg-native", "disagg-trtllm-native",  "Disaggregated", "Native"),
    ("disagg-kvbm",   "disagg-trtllm-kvbm",    "Disaggregated", "KVBM"),
]

def runtime_rps(d):
    log = open(os.path.join(BASE, d, "perf", "load_test.log")).read()
    rt  = float(re.search(r"runtime_sec = ([\d.]+)", log).group(1))
    rps = float(re.search(r"requests_per_sec = ([\d.]+)", log).group(1))
    return rt, rps

def pct(a, p): return float(np.percentile(a, p))

rows = []
for label, d, serving, kv in CONFIGS:
    s = json.load(open(os.path.join(BASE, d, "perf", "multi_turn_stats.json")))
    ttft = np.array([r["ttft_ms"] for r in s])
    tpot = np.array([r["tpot_ms"] for r in s])
    lat  = np.array([r["latency_ms"] for r in s])
    out  = np.array([r["output_num_tokens"] for r in s])
    rt, rps = runtime_rps(d)
    total_out = out.sum()
    rows.append(dict(
        label=label, serving=serving, kv=kv, n=len(s),
        runtime=rt, rps=rps,
        out_tok_s=total_out/rt,
        ttft_mean=ttft.mean(), ttft_p50=pct(ttft,50), ttft_p95=pct(ttft,95), ttft_p99=pct(ttft,99),
        tpot_mean=tpot.mean(), tpot_p50=pct(tpot,50), tpot_p95=pct(tpot,95), tpot_p99=pct(tpot,99),
        lat_mean=lat.mean(),  lat_p50=pct(lat,50),   lat_p95=pct(lat,95),   lat_p99=pct(lat,99),
        ttft=ttft, tpot=tpot, lat=lat,
    ))

# ---- print markdown table ----
def f(x): return f"{x:,.1f}"
print("\n| Config | Serving | KV mgr | Runtime(s) | RPS | Out tok/s | TTFT p50 | TTFT p95 | TTFT p99 | TPOT mean | TPOT p95 | E2E p50 | E2E p95 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['label']} | {r['serving']} | {r['kv']} | {f(r['runtime'])} | {r['rps']:.3f} | {f(r['out_tok_s'])} "
          f"| {f(r['ttft_p50'])} | {f(r['ttft_p95'])} | {f(r['ttft_p99'])} | {r['tpot_mean']:.2f} | {r['tpot_p95']:.2f} "
          f"| {f(r['lat_p50'])} | {f(r['lat_p95'])} |")

# save table data as json for reference
json.dump([{k:v for k,v in r.items() if k not in ('ttft','tpot','lat')} for r in rows],
          open(os.path.join(BASE,"summary.json"),"w"), indent=2)

# ===================== PLOTS =====================
labels = [r["label"] for r in rows]
colors = {"agg-native":"#4C72B0","agg-kvbm":"#55A868","disagg-native":"#C44E52","disagg-kvbm":"#8172B3"}
clist  = [colors[l] for l in labels]

plt.rcParams.update({"figure.dpi":130, "font.size":10})

# ---- Figure 1: throughput dashboard (runtime, rps, out tok/s) ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
metrics = [("runtime","Total runtime (s) — lower is better","s"),
           ("rps","Requests / sec — higher is better",""),
           ("out_tok_s","Output tokens / sec — higher is better","")]
for ax,(key,title,unit) in zip(axes, metrics):
    vals=[r[key] for r in rows]
    bars=ax.bar(labels, vals, color=clist)
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis='x', rotation=20)
    for b,v in zip(bars,vals):
        ax.text(b.get_x()+b.get_width()/2, v, f"{v:,.1f}", ha='center', va='bottom', fontsize=9)
    ax.margins(y=0.15)
fig.suptitle("gpt-oss-120b / TRT-LLM — Throughput & system-level metrics", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(BASE,"plot_throughput.png"), bbox_inches='tight')

# ---- Figure 2: latency percentile grouped bars (TTFT, TPOT, E2E) ----
fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
x = np.arange(len(labels)); w=0.2
pgroups=[("ttft","TTFT (ms) — lower is better"),
         ("tpot","TPOT (ms/token) — lower is better"),
         ("lat","End-to-end latency (ms) — lower is better")]
for ax,(pre,title) in zip(axes,pgroups):
    for i,p in enumerate(["p50","p95","p99"]):
        vals=[r[f"{pre}_{p}"] for r in rows]
        ax.bar(x+(i-1)*w, vals, w, label=p.upper())
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_title(title, fontsize=11); ax.legend(fontsize=8)
fig.suptitle("gpt-oss-120b / TRT-LLM — Latency percentiles (p50 / p95 / p99)", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(BASE,"plot_latency_percentiles.png"), bbox_inches='tight')

# ---- Figure 3: TTFT distribution (CDF) ----
fig, (ax1,ax2)=plt.subplots(1,2,figsize=(14,5))
for r in rows:
    d=np.sort(r["ttft"]); cdf=np.arange(1,len(d)+1)/len(d)
    ax1.plot(d/1000, cdf, label=r["label"], color=colors[r["label"]], lw=2)
ax1.set_xlabel("TTFT (s)"); ax1.set_ylabel("Cumulative fraction of requests")
ax1.set_title("TTFT CDF — leftmost curve is best"); ax1.legend(); ax1.grid(alpha=.3)
ax1.axhline(0.95, ls='--', c='gray', lw=.8); ax1.text(ax1.get_xlim()[1]*.6,0.955,"p95",color='gray',fontsize=8)

for r in rows:
    d=np.sort(r["tpot"]); cdf=np.arange(1,len(d)+1)/len(d)
    ax2.plot(d, cdf, label=r["label"], color=colors[r["label"]], lw=2)
ax2.set_xlabel("TPOT (ms/token)"); ax2.set_ylabel("Cumulative fraction of requests")
ax2.set_title("TPOT CDF — leftmost curve is best"); ax2.legend(); ax2.grid(alpha=.3)
fig.suptitle("gpt-oss-120b / TRT-LLM — Per-request latency distributions", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig(os.path.join(BASE,"plot_distributions.png"), bbox_inches='tight')

print("\nSaved: plot_throughput.png, plot_latency_percentiles.png, plot_distributions.png, summary.json")
