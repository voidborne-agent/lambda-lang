# Lambda Lang Benchmark Results

## Dataset
- **24 samples** across 3 categories
- Categories: task dispatch (8), A2A protocol (8), evolution (8)

## Overall Results

| Metric | Lambda vs Natural Language | Lambda vs JSON |
|--------|---------------------------|----------------|
| Character compression | **2.8x** smaller | **4.7x** smaller |
| Semantic fidelity | **73%** | — |

## Per Category

| Category | vs NL (chars) | vs JSON (chars) | Fidelity |
|----------|:------------:|:---------------:|:--------:|
| task_dispatch | 3.7x | 6.3x | 74% |
| a2a_protocol | 2.4x | 4.1x | 72% |
| evolution | 2.4x | 3.7x | 73% |

## Latency

| Operation | Time |
|-----------|------|
| Encode (EN→Λ) | 159 μs |
| Decode (Λ→EN) | 25 μs |
| Roundtrip | 183 μs |
| JSON parse (baseline) | 2 μs |

## Long-Context Benchmark

Two multi-message conversations simulating real agent workflows:

| Conversation | Messages | NL chars | Λ chars | JSON chars |
|-------------|----------|----------|---------|------------|
| Task orchestration | 38 | 1,307 | 677 | 2,039 |
| Evolution cycle | 28 | 1,131 | 561 | 1,631 |
| **Total** | **66** | **2,438** | **1,238** | **3,670** |

### Long-Context Compression

| Metric | Lambda vs NL | Lambda vs JSON |
|--------|:------------:|:--------------:|
| Characters | **2.0x** smaller | **3.0x** smaller |

### Accumulation Curve (Task Orchestration)

| Messages | NL chars | Λ chars | Compression ratio |
|----------|----------|---------|:-----------------:|
| 10 | 407 | 223 | 1.8x |
| 20 | 756 | 429 | 1.8x |
| 30 | 1,059 | 581 | 1.8x |
| 38 | 1,307 | 677 | 1.9x |

### Why Character Compression Matters

Lambda's value is in **raw character/byte reduction**:

- **Network bandwidth**: HTTP, MQTT, WebSocket — all byte-counted. 2-5x smaller payloads mean faster, cheaper transport.
- **Storage**: Logs, conversation history, database records — all shrink proportionally.
- **Context windows**: Shorter messages mean more conversation fits in fixed-size context.
- **Parsing speed**: Shorter strings parse faster. Lambda's structured format enables deterministic O(n) parsing vs ambiguous NL.

The compression comes from removing human-language redundancy (articles, conjugation, filler words) and replacing multi-character words with 2-char atoms that carry equivalent semantic weight.

### Implication for Real Use

| Transport | Lambda advantage |
|-----------|-----------------|
| HTTP/MQTT/WebSocket (byte-counted) | **2-5x bandwidth savings** |
| Database / log storage | **2-3x storage savings** |
| Agent-to-agent (both speak Λ) | **2x smaller + unambiguous parsing** |
| Structured protocols (replacing JSON) | **3-5x smaller** |

## Methodology
- Character count: UTF-8 encoded byte length
- Semantic fidelity: keyword overlap between original and Lambda decode, with synonym matching
- Latency: average of 100 iterations after 10 warmup rounds
