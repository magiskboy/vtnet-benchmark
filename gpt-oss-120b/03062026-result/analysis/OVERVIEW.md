# gpt-oss-120b trên TRT-LLM — Tổng hợp & Phân tích Benchmark

**Nguồn dữ liệu:** `results/03062026-gpt-oss-120b-trtllm` · **Ngày:** 2026-06-03
**Đã loại trừ:** `agg-trtllm-native`

---

## 1. Bối cảnh: workload giống hệt nhau ⇒ so sánh công bằng

Cả 4 cấu hình chạy **cùng một dataset**, nên mọi khác biệt đến từ kiến trúc serving chứ không phải từ tải:

| Tham số | Giá trị |
|---|---|
| Model | gpt-oss-120b |
| Số request | 1.200 |
| Clients đồng thời | 40 |
| Lượt/hội thoại (trung bình) | ~30 (1–59) |
| Input tokens (trung bình) | ~72.500 |
| Output tokens (trung bình) | ~894 |
| KV cache hit | 93,6% |

> Hậu tố `-p95` chỉ là nhãn tên lần chạy, **không** phải workload khác.

4 cấu hình = tổ hợp 2 trục: **Aggregated vs Disaggregated** × **Native KV vs KVBM** (KV Block Manager).

---

## 2. Bảng tổng hợp

| Config | Serving | KV mgr | Runtime(s) | RPS | Out tok/s | TTFT p50 | TTFT p95 | TPOT mean | TPOT p95 | E2E p50 | E2E p95 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| agg-native | Aggregated | Native | 763,9 | 1,571 | 1.404 | 5.755 | 7.458 | 21,5 | 25,3 | 24.607 | 27.129 |
| agg-kvbm | Aggregated | KVBM | **2.695,4** | **0,445** | **398** | 2.554 | 8.115 | **96,5** | **128,4** | **89.367** | **119.322** |
| disagg-native | Disaggregated | Native | 844,1 | 1,422 | 1.271 | **13.474** | **43.878** | 10,6 | 12,9 | 23.011 | 52.111 |
| **disagg-kvbm** | Disaggregated | KVBM | **507,5** | **2,364** | **2.114** | 3.351 | 9.606 | 14,0 | 16,3 | **16.334** | **20.538** |

*(đơn vị ms trừ khi ghi rõ; **đậm** = tốt nhất / tệ nhất của cột)*

---

## 3. Biểu đồ

### 3.1. Throughput & chỉ số hệ thống
![Throughput](images/plot_throughput.png)

### 3.2. Latency theo percentile (p50 / p95 / p99)
![Latency percentiles](images/plot_latency_percentiles.png)

### 3.3. Phân phối per-request (CDF của TTFT & TPOT)
![Distributions](images/plot_distributions.png)

---

## 4. Insight chính

1. **🏆 `disagg-kvbm` thắng tuyệt đối.** Nhanh nhất ở gần như mọi chỉ số: throughput cao nhất (2,36 RPS, 2.114 tok/s — **~1,5× agg-native**, **~5,3× agg-kvbm**), E2E latency thấp nhất, TTFT/TPOT tốt và ổn định (đuôi p95/p99 hẹp). → **Cấu hình nên triển khai.**

2. **💥 `agg-kvbm` là thảm họa — đừng dùng.** Chậm nhất mọi mặt: runtime 2.695s (>5× disagg-kvbm), TPOT trung bình 96,5 ms/token (~7× chậm hơn), E2E p95 ~119s. KVBM ghép với serving aggregated gây nghẽn nghiêm trọng ở giai đoạn decode (đường xanh lá tách hẳn sang phải trong CDF của TPOT).

3. **KVBM giúp disagg nhưng hại agg.** Cùng chuyển Native → KVBM:
   - **Disaggregated:** cải thiện vượt bậc (runtime 844→508s, RPS 1,42→2,36). KVBM khắc phục đúng điểm yếu của disagg-native.
   - **Aggregated:** phá hỏng hiệu năng (764→2.695s).
   → Lợi ích của KVBM **phụ thuộc kiến trúc**, không phải "bật là tốt".

4. **`disagg-native` có vấn đề TTFT.** Throughput ổn nhưng **TTFT cực tệ và biến động lớn**: p50 13,5s, p95 ~44s, p99 ~53s (đường đỏ trải dài trong TTFT CDF). Bù lại TPOT tốt nhất (10,6 ms). Dấu hiệu nghẽn ở khâu prefill / điều phối KV cache giữa prefill và decode workers — chính là vấn đề KVBM giải quyết được.

5. **Đánh đổi TTFT ↔ TPOT.** Aggregated: TTFT thấp & ổn định nhưng TPOT cao. Disaggregated (native): TPOT thấp nhưng trả giá bằng TTFT. `disagg-kvbm` là cấu hình **duy nhất phá vỡ được đánh đổi này** — tốt ở cả hai.

---

## 5. Khuyến nghị

- ✅ **Production: chọn `disagg-trtllm-kvbm`** — tốt nhất cả throughput lẫn latency đuôi.
- ❌ **Tránh `agg + kvbm`** — phản tác dụng nghiêm trọng.
- ⚠️ Nếu buộc dùng disaggregated, **bắt buộc bật KVBM**; nếu không TTFT sẽ không chấp nhận được.

---

## 6. File trong thư mục này

| File | Mô tả |
|---|---|
| `OVERVIEW.md` | Tài liệu này |
| `images/plot_throughput.png` | Runtime / RPS / output tok/s |
| `images/plot_latency_percentiles.png` | TTFT / TPOT / E2E theo p50·p95·p99 |
| `images/plot_distributions.png` | CDF của TTFT & TPOT (xem rõ phần đuôi) |
| `summary.json` | Số liệu thô đã tính |

> Script tái lập: `results/03062026-gpt-oss-120b-trtllm/analyze.py`
