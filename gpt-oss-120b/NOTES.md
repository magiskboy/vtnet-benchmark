# GPT-OSS-120B benchmark notes

## Bench Job (`bench.yaml`)

- File độc lập ở repo root, không bundle vào các yaml triển khai Dynamo.
- Apply sau khi `llm-bench-frontend` ready: `kubectl apply -f bench.yaml`
- Image: `10.29.252.145:5000/vllm-bench:exp04` (multi-turn scripts trong image).
- Kết quả trên host: `/mnt/models/nkthanh/<BENCHMARK_STACK>/<timestamp>/perf/`
- Patched script: Job ghi file bằng `cat <<'PATCHED_BENCH_EOF'` (nội dung embed trong `bench.yaml`) trước khi chạy benchmark — **không dùng ConfigMap**.
- Sửa patch: chỉnh `gpt-oss-120b/benchmark_serving_multi_turn.py`, rồi regenerate `bench.yaml` (Python one-liner trong repo hoặc copy script vào heredoc block của Job).

## `DISABLE_CONVERSATION_ID`

Script `benchmark_serving_multi_turn.py` (patched, ghi vào pod lúc start Job) mặc định gửi field `conversation_id` trong body `/v1/chat/completions`.

**Dynamo frontend** (TensorRT-LLM) validate chặt OpenAI API và trả **400**:

```text
Validation: Unsupported parameter(s): `conversation_id`
```

Hệ quả: mọi client `num_successes=0`, log `Collected 0 samples from all the clients`.

| Giá trị env | Hành vi |
|-------------|---------|
| `1` / `true` / `yes` | Không gửi `conversation_id` lên API (dùng cho Dynamo) |
| unset / `0` | Gửi `conversation_id` (tương thích PD router native vLLM) |

Bench GPT-OSS Dynamo: set `DISABLE_CONVERSATION_ID=1` và `REASONING_EFFORT=low`.

`disagg-trtllm-native.yaml`: worker dùng `--dyn-reasoning-parser gpt_oss` + `--dyn-tool-call-parser harmony`.

## Endpoint & model

Endpoint benchmark **cố định** cho mọi stack (xem `AGENTS.md`):

| Biến | Giá trị |
|------|---------|
| `URL` | `http://llm-bench-frontend:8000` |

Đổi stack benchmark: sửa `MODEL`, `SERVED_MODEL_NAME`, `BENCHMARK_STACK`, `DISABLE_CONVERSATION_ID`, `REASONING_EFFORT` — **không đổi `URL`**.

| Stack | `MODEL` | `SERVED_MODEL_NAME` | `DISABLE_CONVERSATION_ID` |
|-------|---------|---------------------|---------------------------|
| GPT-OSS Dynamo | `/mnt/models/hf/gpt-oss-120b` | `openai/gpt-oss-120b` | `1` |
| DeepSeek native | `/mnt/models/hf/DeepSeek-V4-Flash-Base` | `deepseek-ai/DeepSeek-V4-Flash-Base` | `0` |

## Triển khai Dynamo (thư mục này)

Tất cả file Dynamo dùng `metadata.name: llm-bench`; service key `frontend` → operator tạo Service `llm-bench-frontend:8000` (convention Dynamo: `<dgd-name>-<service-key>`). Phân biệt stack qua label `benchmark.kvcache/stack`, không qua tên DGD.

### TensorRT-LLM

- Chỉ apply **một** file: `agg-trtllm-native.yaml` | `agg-trtllm-kvbm.yaml` | `disagg-trtllm-native.yaml` | `disagg-trtllm-kvbm.yaml` | `disagg-trtllm-lmcache.yaml`

### vLLM

- Image worker/frontend: `nvcr.io/nvidia/ai-dynamo/vllm-runtime:1.1.1`
- Chỉ apply **một** file: `agg-vllm-native.yaml` | `agg-vllm-kvbm.yaml` | `disagg-vllm-native.yaml` | `disagg-vllm-kvbm.yaml` | `disagg-vllm-lmcache.yaml`

| Pattern | KV tier | Disagg transfer |
|---------|---------|-----------------|
| `*-native` | GPU + prefix cache (`--enable-prefix-caching`) | `NixlConnector` |
| `*-kvbm` | `DYN_KVBM_CPU_CACHE_GB` + `DynamoConnector` / `PdConnector` | prefill: KVBM+NIXL; decode: `NixlConnector` |
| `disagg-*-lmcache` | `LMCACHE_*` CPU tier 1024 GiB (`LMCACHE_MAX_LOCAL_CPU_SIZE`) | prefill: LMCache+NIXL; decode: NIXL / DEFAULT transceiver |

- Disagg LMCache: `disagg-vllm-lmcache.yaml` | `disagg-trtllm-lmcache.yaml` (chỉ apply một stack).
- TRT-LLM LMCache: `kv_connector_config` → `lmcache.integration.tensorrt_llm.tensorrt_adapter` ([LMCache TRT-LLM](https://docs.lmcache.ai/integrations/tensorrt_llm.html)); cần `uv pip install lmcache` trên prefill pod.
- vLLM LMCache: prefill `PdConnector` (`LMCacheConnectorV1` + `NixlConnector`) theo `disagg_lmcache.sh` Dynamo.

- Node pin: `hla9104p1-escn8-smt-hgx47`
