# Lambda Lang Benchmark Results

## Dataset
- **208 samples** across 8 categories
- Categories: task_dispatch (26), a2a_protocol (26), evolution (26), error_handling (26), session_management (26), monitoring (26), coordination (26), data_exchange (26)

## Overall Results

| Metric | Lambda vs Natural Language | Lambda vs JSON |
|--------|---------------------------|----------------|
| Character compression | **3.0x** smaller | **4.6x** smaller |
| Byte compression | **3.0x** smaller | **4.6x** smaller |

| Metric | Value |
|--------|-------|
| Semantic fidelity | **28%** |
| Encode latency | 162 μs |
| Decode latency | 24 μs |
| Roundtrip | 186 μs |

## Per Category

| Category | vs NL (chars) | vs JSON (chars) | vs NL (bytes) | vs JSON (bytes) | Fidelity |
|----------|:------------:|:---------------:|:------------:|:---------------:|:--------:|
| task_dispatch | 3.2x | 5.3x | 3.2x | 5.3x | 38% |
| a2a_protocol | 2.6x | 4.4x | 2.6x | 4.4x | 37% |
| evolution | 2.6x | 4.2x | 2.6x | 4.2x | 39% |
| error_handling | 3.2x | 4.7x | 3.2x | 4.7x | 23% |
| session_management | 3.2x | 5.3x | 3.2x | 5.3x | 34% |
| monitoring | 3.1x | 4.6x | 3.1x | 4.6x | 8% |
| coordination | 3.2x | 4.6x | 3.2x | 4.6x | 16% |
| data_exchange | 2.8x | 4.1x | 2.8x | 4.1x | 24% |

## Latency

| Operation | Time |
|-----------|------|
| Encode (EN→Λ) | 162 μs |
| Decode (Λ→EN) | 24 μs |
| Roundtrip | 186 μs |
| JSON parse (baseline) | 2 μs |

## Methodology
- Character count: string length
- Byte count: UTF-8 encoded length
- Semantic fidelity: keyword overlap between original and Lambda decode, with synonym matching
- Latency: average of 100 iterations after 10 warmup rounds
