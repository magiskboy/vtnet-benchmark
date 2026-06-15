# DeepSeek-V4-Flash — Báo cáo benchmark vLLM (10/06/2026)

So sánh hai biến thể model **DeepSeek-V4-Flash** trên stack **vLLM disaggregated** (prefill/decode tách rời, KV transfer qua NixlConnector) trên hạ tầng DGX-H200.

| Config | Model weights | Quantization | Topology | Run ID |
|---|---|---|---|---|
| `deepseek-flash-fp4` | `DeepSeek-V4-Flash` | FP8 weights + FP8 KV cache | 2-node PD (prefill hgx46, decode hgx47), DP=8 | `20260610T075958` |
| `deepseek-flash-base-fp8` | `DeepSeek-V4-Flash-Base` | FP8 weights + FP8 KV cache | Single-node PD (hgx47), DP=4 prefill | `20260611T015457` |

Backend: **vLLM v0.22.0** · Serving: **Disaggregated** · KV manager: **Native (Nixl)**

---

## Kịch bản load test

Cả hai run dùng cùng workload multi-turn:

| Tham số | Giá trị |
|---|---|
| Số client / conversation | 40 / 40 |
| Số turn mỗi conversation | 30 |
| Turn đầu (prefix) | 20 000 + 10 000 token ngẫu nhiên ≈ **30 000 token** |
| Turn tiếp theo | **2 048 token** / turn |
| Output mỗi request | **900 token** (cố định) |
| Request rate | Không giới hạn (burst tối đa) |
| Streaming | Bật |

Workload mô phỏng hội thoại dài với context lớn — phù hợp đánh giá prefill nặng và KV cache multi-turn.

---

## Kết quả tổng hợp

| Config | Requests | Runtime (s) | RPS | Out tok/s | TTFT p50 (ms) | TTFT p95 (ms) | TPOT mean (ms) | E2E p50 (ms) | E2E p95 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `deepseek-flash-fp4` | 958 | 2 241.8 | 0.427 | 384.5 | 54 661 | 140 487 | 11.92 | 65 312 | 150 012 |
| `deepseek-flash-base-fp8` | 1 200 | 1 939.8 | 0.619 | 556.6 | 50 063 | 81 205 | 16.44 | 65 087 | 96 121 |

> **Lưu ý hoàn thành:** run `deepseek-flash-fp4` chỉ hoàn tất **15/40 conversation** (958/1 200 request dự kiến), nhiều request bị timeout trong điều kiện tải cao. Run `deepseek-flash-base-fp8` hoàn tất đủ **40/40 conversation**. Khi so sánh throughput và tail latency cần tính đến sự khác biệt này.

---

## Phân tích

### Throughput

`deepseek-flash-base-fp8` vượt trội rõ rệt về throughput hệ thống:

- **Runtime** giảm ~13% (2 242 s → 1 940 s)
- **RPS** tăng ~45% (0.43 → 0.62 req/s)
- **Output throughput** tăng ~45% (385 → 557 tok/s)

![Throughput & system-level metrics](images/plot_throughput.png)

### Latency — trade-off TTFT vs TPOT

Hai config thể hiện profile latency đối lập:

**Time to First Token (TTFT)** — `base-fp8` tốt hơn, đặc biệt ở tail:

| Percentile | fp4 (ms) | base-fp8 (ms) | Cải thiện |
|---:|---:|---:|---:|
| p50 | 54 661 | 50 063 | ~8% |
| p95 | 140 487 | 81 205 | ~42% |
| p99 | 164 997 | 86 596 | ~48% |

**Time Per Output Token (TPOT)** — `fp4` nhanh hơn đáng kể khi đã bắt đầu decode:

| Percentile | fp4 (ms/tok) | base-fp8 (ms/tok) | fp4 nhanh hơn |
|---:|---:|---:|---:|
| mean | 11.92 | 16.44 | ~27% |
| p95 | 13.86 | 17.97 | ~23% |

**End-to-end latency:**

- **p50** gần tương đương (~65 s) — phần lớn thời gian là generate 900 token.
- **p95/p99** — `base-fp8` ổn định hơn nhiều: p95 giảm ~36% (150 s → 96 s), p99 giảm ~42% (174 s → 101 s).

![Latency percentiles](images/plot_latency_percentiles.png)

Phân phối CDF cho thấy rõ sự tách biệt: `base-fp8` thắng ở TTFT (đường CDF dịch trái), `fp4` thắng ở TPOT.

![Per-request latency distributions](images/plot_distributions.png)

### Trade-off throughput vs tail latency

Trên biểu đồ throughput (trục X) vs E2E p95 (trục Y), `deepseek-flash-base-fp8` nằm ở vùng tối ưu (góc dưới-phải): throughput cao hơn ~45% đồng thời tail latency thấp hơn ~36%.

![Throughput vs tail-latency trade-off](images/plot_tradeoff.png)

---

## Kết luận

| Tiêu chí | Khuyến nghị |
|---|---|
| **Throughput tổng thể & độ ổn định** | `deepseek-flash-base-fp8` — nhanh hơn, hoàn thành đủ workload, tail latency thấp |
| **TTFT / phản hồi đầu** | `deepseek-flash-base-fp8` — p95 TTFT thấp hơn ~42% |
| **Tốc độ generate (TPOT)** | `deepseek-flash-fp4` — ~23–27% nhanh hơn mỗi output token |
| **Độ tin cậy dưới tải cao** | `deepseek-flash-base-fp8` — hoàn tất 100% conversation; fp4 bị timeout một phần |

**Tóm lại:** Với workload multi-turn context dài (30k token turn đầu, 40 client đồng thời), **`DeepSeek-V4-Flash-Base` + FP8 trên topology single-node** cho kết quả tổng thể tốt hơn `DeepSeek-V4-Flash` trên topology 2-node. Mặc dù Flash variant decode nhanh hơn từng token, overhead TTFT cao và khả năng chịu tải kém hơn khiến throughput thực tế và tail latency kém hơn đáng kể.

---

## Hạn chế & bước tiếp theo

1. **Không apples-to-apples hoàn toàn** — khác topology (2-node vs single-node), khác DP size (8 vs 4), và mức hoàn thành workload.
2. **Cần rerun `deepseek-flash-fp4`** với cùng topology hoặc tăng timeout để có 1 200 request đầy đủ, giúp so sánh công bằng hơn.
3. Chưa đo chất lượng output (accuracy/perplexity) — chỉ đánh giá hiệu năng serving.
4. Có thể thử thêm: aggregated serving, KVBM, sweep concurrency (10/20/40 client).

---

## Tài liệu tham chiếu

- Cấu hình phân tích: [`configs/deepseek-flash-10062026.json`](../../configs/deepseek-flash-10062026.json)
- Dữ liệu thô: `deepseek-v4-flash/10062026-result/{20260610T075958,20260611T015457}/perf/`
- YAML deploy: `deepseek-v4-flash/disagg-vllm-native.yaml` (fp4), `disagg-vllm-native-single-node.yaml` (base-fp8)
- Metrics JSON: [`summary.json`](summary.json)
