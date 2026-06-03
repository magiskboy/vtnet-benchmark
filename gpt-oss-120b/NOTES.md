# GPT-OSS-120B benchmark notes

## Bench Job (`bench.yaml`)

- File độc lập ở repo root, không bundle vào các yaml triển khai Dynamo.
- Apply sau khi stack `gpt-oss-trtllm` ready: `kubectl apply -f bench.yaml`
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
| unset / `0` | Gửi `conversation_id` (tương thích endpoint/router cũ, ví dụ `bench-exp04`) |

Job trong `bench.yaml` set `DISABLE_CONVERSATION_ID=1` và `REASONING_EFFORT=low` (gửi qua `chat_template_args` trong request).

`disagg-trtllm-native.yaml`: worker dùng `--dyn-reasoning-parser gpt_oss` + `--dyn-tool-call-parser harmony`.

## Endpoint & model

| Biến | Giá trị hiện tại |
|------|------------------|
| `URL` | `http://gpt-oss-trtllm-frontend:8000` |
| `SERVED_MODEL_NAME` | `openai/gpt-oss-120b` |
| `MODEL` (tokenizer path) | `/mnt/models/hf/gpt-oss-120b` |

Đổi stack benchmark: sửa `BENCHMARK_STACK` (tên thư mục kết quả), không cần đổi tên deployment.

## Triển khai Dynamo (thư mục này)

- `metadata.name`: `gpt-oss-trtllm` → frontend DNS: `gpt-oss-trtllm-frontend:8000`
- Chỉ apply **một** file deployment tại một thời điểm (disagg-kvbm / disagg-native / agg-kvbm / agg-native).
- Node pin: `hla9104p1-escn8-smt-hgx47`
