# Lambda Lang Benchmark Results

## Dataset
- **24 samples** across 3 categories
- Categories: task dispatch (8), A2A protocol (8), evolution (8)

## Overall Results

| Metric | Lambda vs Natural Language | Lambda vs JSON |
|--------|---------------------------|----------------|
| Byte compression | **2.8x** smaller | **4.7x** smaller |
| Token compression | **1.0x** fewer | **2.2x** fewer |

| Metric | Value |
|--------|-------|
| Semantic fidelity | **73%** |
| Encode latency | 159 μs |
| Decode latency | 25 μs |
| Roundtrip | 183 μs |

## Per Category

| Category | vs NL (bytes) | vs NL (tokens) | vs JSON (bytes) | vs JSON (tokens) | Fidelity |
|----------|--------------|----------------|-----------------|-------------------|----------|
| task_dispatch | 3.7x | 1.4x | 6.3x | 3.2x | 74% |
| a2a_protocol | 2.4x | 0.8x | 4.1x | 1.9x | 72% |
| evolution | 2.4x | 0.8x | 3.7x | 1.6x | 73% |

## Latency

| Operation | Time |
|-----------|------|
| Encode (EN→Λ) | 159 μs |
| Decode (Λ→EN) | 25 μs |
| Roundtrip | 183 μs |
| JSON parse (baseline) | 2 μs |

## Long-Context Benchmark

Two multi-message conversations simulating real agent workflows:

| Conversation | Messages | NL bytes | Λ bytes | JSON bytes |
|-------------|----------|----------|---------|------------|
| Task orchestration | 38 | 1,307 | 677 | 2,039 |
| Evolution cycle | 28 | 1,131 | 561 | 1,631 |
| **Total** | **66** | **2,438** | **1,238** | **3,670** |

### Long-Context Compression

| Metric | Lambda vs NL | Lambda vs JSON |
|--------|:------------:|:--------------:|
| Bytes | **2.0x** smaller | **3.0x** smaller |
| Tokens (cl100k) | 0.9x (Lambda uses more) | **1.6x** fewer |

### Accumulation Curve (Task Orchestration)

| Messages | NL bytes | Λ bytes | Byte ratio | NL tokens | Λ tokens | Token ratio |
|----------|----------|---------|:----------:|-----------|----------|:-----------:|
| 10 | 407 | 223 | 1.8x | 94 | 97 | 1.0x |
| 20 | 756 | 429 | 1.8x | 167 | 190 | 0.9x |
| 30 | 1,059 | 581 | 1.8x | 239 | 263 | 0.9x |
| 38 | 1,307 | 677 | 1.9x | 292 | 308 | 0.9x |

### Why Tokens Don't Improve

LLM tokenizers (cl100k_base) are optimized for English:
- `"Node heartbeat OK"` → 3 tokens (words merge well)
- `"!nd hb ok"` → 4 tokens (each atom is a separate token)
- `{"type":"heartbeat","status":"ok"}` → 9 tokens (JSON syntax overhead)

Lambda atoms are too short for the tokenizer to merge efficiently. Each 2-char atom becomes its own token, same as a full English word. **Lambda's value is in bytes and semantics, not in LLM token economy vs English.**

However, **vs JSON, Lambda consistently saves tokens (1.6x)** because JSON's quote/colon/brace syntax is even worse for tokenizers.

### Implication for Real Use

| Transport | Lambda advantage |
|-----------|-----------------|
| HTTP/MQTT/file (byte-counted) | **2-3x bandwidth savings** |
| LLM context (replacing JSON protocols) | **1.6x token savings** |
| LLM context (replacing English) | **No token savings** — use English |
| Agent-to-agent (both speak Λ) | **2x byte savings + unambiguous parsing** |

## Methodology
- Byte count: UTF-8 encoded length
- Token count: tiktoken cl100k_base (GPT-4)
- Semantic fidelity: keyword overlap between original and Lambda decode, with synonym matching
- Latency: average of 100 iterations after 10 warmup rounds
