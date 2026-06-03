## disagg-trtllm-kvbm

```
============ Serving Benchmark Result ============
Successful requests:                     200
Failed requests:                         0
Maximum request concurrency:             30
Benchmark duration (s):                  326.39
Total input tokens:                      4000000
Total generated tokens:                  1000000
Request throughput (req/s):              0.61
Output token throughput (tok/s):         3063.85
Peak output token throughput (tok/s):    4605.00
Peak concurrent requests:                32.00
Total token throughput (tok/s):          15319.27
---------------Time to First Token----------------
Mean TTFT (ms):                          3402.84
Median TTFT (ms):                        1303.56
P50 TTFT (ms):                           1303.56
P90 TTFT (ms):                           10877.93
P99 TTFT (ms):                           22712.80
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.68
Median TPOT (ms):                        8.77
P50 TPOT (ms):                           8.77
P90 TPOT (ms):                           8.85
P99 TPOT (ms):                           8.90
---------------Inter-token Latency----------------
Mean ITL (ms):                           8.68
Median ITL (ms):                         8.50
P50 ITL (ms):                            8.50
P90 ITL (ms):                            12.89
P99 ITL (ms):                            21.33
==================================================
```

## disagg-trtllm-native

```
============ Serving Benchmark Result ============
Successful requests:                     200
Failed requests:                         0
Maximum request concurrency:             30
Benchmark duration (s):                  344.63
Total input tokens:                      4000000
Total generated tokens:                  1000000
Request throughput (req/s):              0.58
Output token throughput (tok/s):         2901.66
Peak output token throughput (tok/s):    3268.00
Peak concurrent requests:                42.00
Total token throughput (tok/s):          14508.30
---------------Time to First Token----------------
Mean TTFT (ms):                          2203.38
Median TTFT (ms):                        842.27
P50 TTFT (ms):                           842.27
P90 TTFT (ms):                           8440.57
P99 TTFT (ms):                           12091.58
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          9.41
Median TPOT (ms):                        9.46
P50 TPOT (ms):                           9.46
P90 TPOT (ms):                           9.63
P99 TPOT (ms):                           9.64
---------------Inter-token Latency----------------
Mean ITL (ms):                           9.41
Median ITL (ms):                         9.29
P50 ITL (ms):                            9.29
P90 ITL (ms):                            13.16
P99 ITL (ms):                            20.51
==================================================
```

## comparison (disagg-trtllm-kvbm vs disagg-trtllm-native)

| Metric | disagg-trtllm-kvbm | disagg-trtllm-native | Better |
|---|---:|---:|---|
| Successful requests | 200 | 200 | Tie |
| Failed requests | 0 | 0 | Tie |
| Benchmark duration (s) | 326.39 | 344.63 | KVBM |
| Request throughput (req/s) | 0.61 | 0.58 | KVBM |
| Output token throughput (tok/s) | 3063.85 | 2901.66 | KVBM |
| Peak output token throughput (tok/s) | 4605.00 | 3268.00 | KVBM |
| Peak concurrent requests | 32.00 | 42.00 | Native |
| Total token throughput (tok/s) | 15319.27 | 14508.30 | KVBM |
| Mean TTFT (ms) | 3402.84 | 2203.38 | Native |
| P50 TTFT (ms) | 1303.56 | 842.27 | Native |
| P90 TTFT (ms) | 10877.93 | 8440.57 | Native |
| P99 TTFT (ms) | 22712.80 | 12091.58 | Native |
| Mean TPOT (ms) | 8.68 | 9.41 | KVBM |
| P50 TPOT (ms) | 8.77 | 9.46 | KVBM |
| P90 TPOT (ms) | 8.85 | 9.63 | KVBM |
| P99 TPOT (ms) | 8.90 | 9.64 | KVBM |
| Mean ITL (ms) | 8.68 | 9.41 | KVBM |
| P50 ITL (ms) | 8.50 | 9.29 | KVBM |
| P90 ITL (ms) | 12.89 | 13.16 | KVBM |
| P99 ITL (ms) | 21.33 | 20.51 | Native |

## agg-trtllm-kvbm

```
```

## agg-trtllm-kvbm

```
```