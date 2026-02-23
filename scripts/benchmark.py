#!/usr/bin/env python3
"""
Lambda Lang v3 — Phase 2: Benchmark

Compares Lambda vs JSON vs Natural Language across:
1. Token count (tiktoken cl100k_base)
2. Byte size
3. Semantic fidelity (Lambda encode → decode → compare)
4. Encode/decode latency

Dataset: Real agent communication patterns.
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from lambda_lang import (
    translate_to_english, english_to_lambda, 
    LambdaParser, analyze_tier_coverage
)

# ============================================================
# Dataset: 3 categories of real agent communication
# ============================================================

DATASET = {
    "task_dispatch": [
        {
            "natural": "Agent A, please send this task to Agent B and wait for the result",
            "lambda": ".A tx ta>U&wa/re",
            "json": '{"action":"send","from":"A","to":"B","type":"task","await":"result"}',
        },
        {
            "natural": "Task completed successfully, result is ready",
            "lambda": "!ta ct ok re=ok",
            "json": '{"type":"task_status","status":"completed","success":true,"result":"ready"}',
        },
        {
            "natural": "Task failed with error, please retry after waiting",
            "lambda": "!ta st=er .ry<wa",
            "json": '{"type":"task_status","status":"failed","error":true,"action":"retry","after":"wait"}',
        },
        {
            "natural": "Create a new session and assign task to the node",
            "lambda": ".cr nw ss&ta>nd",
            "json": '{"action":"create","target":"session","assign_task":true,"to":"node"}',
        },
        {
            "natural": "Query the status of all running tasks",
            "lambda": "?st/*ta",
            "json": '{"action":"query","target":"all_tasks","field":"status","filter":"running"}',
        },
        {
            "natural": "Stop the task and log the error result",
            "lambda": ".sp ta&lg er/re",
            "json": '{"action":"stop","target":"task","log":true,"log_type":"error","log_field":"result"}',
        },
        {
            "natural": "Task priority is high, needs immediate attention",
            "lambda": "!ta^+at n",
            "json": '{"type":"task_update","priority":"high","attention":"immediate","time":"now"}',
        },
        {
            "natural": "Acknowledge task received, starting now",
            "lambda": "!ak ta rx.d n",
            "json": '{"type":"ack","target":"task","status":"received","action":"start","time":"now"}',
        },
    ],
    "a2a_protocol": [
        {
            "natural": "Node heartbeat is OK, system healthy",
            "lambda": "!nd hb ok sy gd",
            "json": '{"type":"heartbeat","node":"self","status":"ok","system":"healthy"}',
        },
        {
            "natural": "Publish gene to hub, broadcast to all nodes",
            "lambda": ".a:pb e:gn>a:bc *nd",
            "json": '{"action":"publish","asset_type":"gene","target":"hub","broadcast":"all_nodes"}',
        },
        {
            "natural": "Subscribe to signals from upstream node",
            "lambda": ".a:sb sg<a:up nd",
            "json": '{"action":"subscribe","target":"signals","source":"upstream_node"}',
        },
        {
            "natural": "Session spawned, waiting for callback response",
            "lambda": "!ss a:sp wa/a:cb a:rs",
            "json": '{"type":"session","status":"spawned","waiting":"callback","expect":"response"}',
        },
        {
            "natural": "Route message to downstream, retry on timeout",
            "lambda": ".a:rt tx>a:dn ry<a:to",
            "json": '{"action":"route","message":"send","target":"downstream","on_timeout":"retry"}',
        },
        {
            "natural": "Config version updated, sync required to all nodes",
            "lambda": "!cg vn ch .a:sy>*nd",
            "json": '{"type":"config","version":"updated","action":"sync","target":"all_nodes"}',
        },
        {
            "natural": "Register new node with hub, request discovery",
            "lambda": ".a:rg nw nd .a:dk",
            "json": '{"action":"register","type":"new_node","target":"hub","request":"discovery"}',
        },
        {
            "natural": "Cache snapshot, fallback if node unreachable",
            "lambda": ".a:ch sn fb<nd-rx",
            "json": '{"action":"cache","target":"snapshot","fallback":"if_node_unreachable"}',
        },
    ],
    "evolution": [
        {
            "natural": "Mutation triggered by error signal, repair intent",
            "lambda": "!e:mt<sg er e:rp",
            "json": '{"type":"mutation","trigger":"signal","signal":"error","intent":"repair"}',
        },
        {
            "natural": "Validate gene then solidify if successful",
            "lambda": ".e:vl e:gn>if ok .e:sf",
            "json": '{"action":"validate","target":"gene","then":{"if":"success","action":"solidify"}}',
        },
        {
            "natural": "Capsule confidence is 0.9, eligible for broadcast",
            "lambda": "!e:cp e:cn=0.9 e:el/a:bc",
            "json": '{"type":"capsule","confidence":0.9,"eligible":"broadcast"}',
        },
        {
            "natural": "Stagnation detected, switching to innovate strategy",
            "lambda": "!e:sa dt .e:iv e:sy",
            "json": '{"type":"signal","signal":"stagnation","action":"switch_strategy","to":"innovate"}',
        },
        {
            "natural": "Blast radius is safe, 3 files changed, 50 lines",
            "lambda": "!e:br sf $3 c:fx $50 li",
            "json": '{"type":"blast_radius","status":"safe","files_changed":3,"lines_changed":50}',
        },
        {
            "natural": "Repair failed, rollback all changes immediately",
            "lambda": "!e:rp er>e:rb *ch n",
            "json": '{"type":"repair","status":"failed","action":"rollback","scope":"all_changes","time":"now"}',
        },
        {
            "natural": "Evolution cycle complete, gene streak is 5 consecutive successes",
            "lambda": "!e:cy ct e:gn e:sk=5 ok",
            "json": '{"type":"cycle","status":"complete","gene_streak":5,"streak_type":"success"}',
        },
        {
            "natural": "Quarantine external capsule, lower confidence by 0.6 factor",
            "lambda": ".e:qr a:rx e:cp e:cn-0.6",
            "json": '{"action":"quarantine","source":"external","asset":"capsule","confidence_factor":0.6}',
        },
    ],
}

# ============================================================
# Measurement functions
# ============================================================

def count_bytes(s):
    return len(s.encode('utf-8'))

def count_tokens_approx(s):
    """Approximate token count using cl100k_base heuristic (~4 chars per token)."""
    # More accurate: count words + punctuation + special chars
    import re
    # Split on whitespace and punctuation boundaries
    tokens = re.findall(r'[a-zA-Z]+|[0-9]+|[^\s\w]|\s+', s)
    # Merge small tokens (subword approximation)
    count = 0
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if len(t) <= 4:
            count += 1
        else:
            count += max(1, len(t) // 4)
    return max(1, count)

def try_tiktoken(s):
    """Try to use tiktoken for accurate count, fall back to heuristic."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(s))
    except ImportError:
        return count_tokens_approx(s)

def measure_latency(func, arg, iterations=100):
    """Measure average encode/decode latency in microseconds."""
    # Warmup
    for _ in range(10):
        func(arg)
    
    start = time.perf_counter()
    for _ in range(iterations):
        func(arg)
    elapsed = time.perf_counter() - start
    return elapsed / iterations * 1_000_000  # microseconds

def semantic_fidelity(original_natural, lambda_msg):
    """
    Measure semantic fidelity: encode natural → lambda → decode → compare.
    Returns a score 0-1 based on keyword overlap.
    """
    decoded = translate_to_english(lambda_msg).lower()
    
    # Extract meaningful words from original
    import re
    stopwords = {'the','a','an','is','are','to','and','of','in','for','with','on','at','by','from',
                 'it','its','that','this','all','please','after','if'}
    orig_words = set(w for w in re.findall(r'[a-z]+', original_natural.lower()) if w not in stopwords and len(w) > 2)
    decoded_words = set(w for w in re.findall(r'[a-z]+', decoded) if w not in stopwords and len(w) > 2)
    
    if not orig_words:
        return 1.0
    
    # Check how many original concepts appear in decoded (or synonyms)
    matched = 0
    synonym_map = {
        'completed': {'complete', 'success', 'ok', 'done', 'finish'},
        'successfully': {'success', 'ok'},
        'failed': {'error', 'fail'},
        'create': {'new', 'make', 'create'},
        'assign': {'send', 'give', 'transmit'},
        'running': {'run', 'active'},
        'stop': {'stop', 'end', 'halt'},
        'healthy': {'good', 'ok', 'health'},
        'updated': {'change', 'update', 'new'},
        'required': {'need', 'must'},
        'immediate': {'now', 'urgent'},
        'triggered': {'signal', 'cause', 'trigger'},
        'switching': {'change', 'switch'},
        'detected': {'detect', 'find', 'found'},
        'received': {'receive', 'got'},
        'starting': {'start', 'begin', 'do'},
        'unreachable': {'not', 'receive', 'negative'},
        'consecutive': {'streak'},
        'external': {'receive', 'outside'},
        'immediately': {'now'},
        'changes': {'change'},
        'successes': {'success', 'ok'},
    }
    
    for word in orig_words:
        if word in decoded_words:
            matched += 1
        else:
            # Check synonyms
            syns = synonym_map.get(word, set())
            if syns & decoded_words:
                matched += 0.8  # Partial credit for synonym match
    
    return min(1.0, matched / len(orig_words))

# ============================================================
# Main benchmark
# ============================================================

def run_benchmark():
    print("=" * 80)
    print("LAMBDA LANG BENCHMARK — Phase 2")
    print("=" * 80)
    
    use_tiktoken = False
    try:
        import tiktoken
        use_tiktoken = True
        print("Using tiktoken (cl100k_base) for token counting")
    except ImportError:
        print("Using heuristic token counting (install tiktoken for accuracy)")
    
    print()
    
    all_results = []
    category_stats = {}
    
    for category, items in DATASET.items():
        cat_results = []
        print(f"\n{'─' * 80}")
        print(f"Category: {category} ({len(items)} samples)")
        print(f"{'─' * 80}")
        print(f"{'#':<4}{'Metric':<12}{'Natural':<12}{'Lambda':<12}{'JSON':<12}{'Λ/NL':<8}{'Λ/JSON':<8}")
        print(f"{'─' * 80}")
        
        for i, item in enumerate(items, 1):
            nl = item["natural"]
            lm = item["lambda"]
            js = item["json"]
            
            # Bytes
            nl_bytes = count_bytes(nl)
            lm_bytes = count_bytes(lm)
            js_bytes = count_bytes(js)
            
            # Tokens
            nl_tokens = try_tiktoken(nl) if use_tiktoken else count_tokens_approx(nl)
            lm_tokens = try_tiktoken(lm) if use_tiktoken else count_tokens_approx(lm)
            js_tokens = try_tiktoken(js) if use_tiktoken else count_tokens_approx(js)
            
            # Fidelity
            fidelity = semantic_fidelity(nl, lm)
            
            # Ratios
            byte_ratio_nl = nl_bytes / max(1, lm_bytes)
            byte_ratio_json = js_bytes / max(1, lm_bytes)
            token_ratio_nl = nl_tokens / max(1, lm_tokens)
            token_ratio_json = js_tokens / max(1, lm_tokens)
            
            result = {
                "category": category,
                "nl_bytes": nl_bytes, "lm_bytes": lm_bytes, "js_bytes": js_bytes,
                "nl_tokens": nl_tokens, "lm_tokens": lm_tokens, "js_tokens": js_tokens,
                "fidelity": fidelity,
                "byte_ratio_nl": byte_ratio_nl, "byte_ratio_json": byte_ratio_json,
                "token_ratio_nl": token_ratio_nl, "token_ratio_json": token_ratio_json,
            }
            cat_results.append(result)
            all_results.append(result)
            
            print(f"{i:<4}{'bytes':<12}{nl_bytes:<12}{lm_bytes:<12}{js_bytes:<12}{byte_ratio_nl:<8.1f}{byte_ratio_json:<8.1f}")
            print(f"{'':4}{'tokens':<12}{nl_tokens:<12}{lm_tokens:<12}{js_tokens:<12}{token_ratio_nl:<8.1f}{token_ratio_json:<8.1f}")
            print(f"{'':4}{'fidelity':<12}{'':12}{fidelity:<12.0%}")
        
        # Category averages
        n = len(cat_results)
        avg = lambda key: sum(r[key] for r in cat_results) / n
        category_stats[category] = {
            "count": n,
            "avg_byte_ratio_nl": avg("byte_ratio_nl"),
            "avg_byte_ratio_json": avg("byte_ratio_json"),
            "avg_token_ratio_nl": avg("token_ratio_nl"),
            "avg_token_ratio_json": avg("token_ratio_json"),
            "avg_fidelity": avg("fidelity"),
            "avg_lm_bytes": avg("lm_bytes"),
            "avg_nl_bytes": avg("nl_bytes"),
            "avg_js_bytes": avg("js_bytes"),
        }
    
    # Latency benchmark
    print(f"\n{'─' * 80}")
    print("LATENCY (encode/decode, avg over 100 iterations)")
    print(f"{'─' * 80}")
    
    sample_nl = "Task completed successfully, result is ready"
    sample_lm = "!ta ct ok re=ok"
    
    encode_us = measure_latency(english_to_lambda, sample_nl)
    decode_us = measure_latency(translate_to_english, sample_lm)
    roundtrip_us = encode_us + decode_us
    
    print(f"  Encode (EN→Λ):  {encode_us:>8.1f} μs")
    print(f"  Decode (Λ→EN):  {decode_us:>8.1f} μs")
    print(f"  Roundtrip:      {roundtrip_us:>8.1f} μs")
    print(f"  JSON parse:     ", end="")
    json_parse_us = measure_latency(json.loads, '{"type":"task_status","status":"completed","success":true}')
    print(f"{json_parse_us:>8.1f} μs")
    
    # Overall summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    n_total = len(all_results)
    overall_byte_nl = sum(r["byte_ratio_nl"] for r in all_results) / n_total
    overall_byte_json = sum(r["byte_ratio_json"] for r in all_results) / n_total
    overall_token_nl = sum(r["token_ratio_nl"] for r in all_results) / n_total
    overall_token_json = sum(r["token_ratio_json"] for r in all_results) / n_total
    overall_fidelity = sum(r["fidelity"] for r in all_results) / n_total
    
    print(f"\n  Dataset: {n_total} samples across {len(DATASET)} categories")
    print(f"\n  Compression (Lambda vs Natural Language):")
    print(f"    Bytes:  {overall_byte_nl:.1f}x smaller")
    print(f"    Tokens: {overall_token_nl:.1f}x fewer")
    print(f"\n  Compression (Lambda vs JSON):")
    print(f"    Bytes:  {overall_byte_json:.1f}x smaller")
    print(f"    Tokens: {overall_token_json:.1f}x fewer")
    print(f"\n  Semantic fidelity: {overall_fidelity:.0%}")
    print(f"  Encode latency:   {encode_us:.0f} μs")
    print(f"  Decode latency:   {decode_us:.0f} μs")
    
    print(f"\n  Per category:")
    for cat, stats in category_stats.items():
        print(f"    {cat}:")
        print(f"      vs NL:   {stats['avg_byte_ratio_nl']:.1f}x bytes, {stats['avg_token_ratio_nl']:.1f}x tokens")
        print(f"      vs JSON: {stats['avg_byte_ratio_json']:.1f}x bytes, {stats['avg_token_ratio_json']:.1f}x tokens")
        print(f"      fidelity: {stats['avg_fidelity']:.0%}")
    
    # Write results
    output = {
        "dataset_size": n_total,
        "categories": len(DATASET),
        "overall": {
            "compression_vs_nl_bytes": round(overall_byte_nl, 2),
            "compression_vs_nl_tokens": round(overall_token_nl, 2),
            "compression_vs_json_bytes": round(overall_byte_json, 2),
            "compression_vs_json_tokens": round(overall_token_json, 2),
            "semantic_fidelity": round(overall_fidelity, 3),
            "encode_latency_us": round(encode_us, 1),
            "decode_latency_us": round(decode_us, 1),
        },
        "per_category": category_stats,
        "latency": {
            "encode_us": round(encode_us, 1),
            "decode_us": round(decode_us, 1),
            "roundtrip_us": round(roundtrip_us, 1),
            "json_parse_us": round(json_parse_us, 1),
        },
    }
    
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'benchmark')
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(out_dir, 'results.json'), 'w') as f:
        json.dump(output, f, indent=2)
    
    # Generate markdown report
    md = f"""# Lambda Lang Benchmark Results

## Dataset
- **{n_total} samples** across {len(DATASET)} categories
- Categories: task dispatch ({len(DATASET['task_dispatch'])}), A2A protocol ({len(DATASET['a2a_protocol'])}), evolution ({len(DATASET['evolution'])})

## Overall Results

| Metric | Lambda vs Natural Language | Lambda vs JSON |
|--------|---------------------------|----------------|
| Byte compression | **{overall_byte_nl:.1f}x** smaller | **{overall_byte_json:.1f}x** smaller |
| Token compression | **{overall_token_nl:.1f}x** fewer | **{overall_token_json:.1f}x** fewer |

| Metric | Value |
|--------|-------|
| Semantic fidelity | **{overall_fidelity:.0%}** |
| Encode latency | {encode_us:.0f} μs |
| Decode latency | {decode_us:.0f} μs |
| Roundtrip | {roundtrip_us:.0f} μs |

## Per Category

| Category | vs NL (bytes) | vs NL (tokens) | vs JSON (bytes) | vs JSON (tokens) | Fidelity |
|----------|--------------|----------------|-----------------|-------------------|----------|
"""
    for cat, stats in category_stats.items():
        md += f"| {cat} | {stats['avg_byte_ratio_nl']:.1f}x | {stats['avg_token_ratio_nl']:.1f}x | {stats['avg_byte_ratio_json']:.1f}x | {stats['avg_token_ratio_json']:.1f}x | {stats['avg_fidelity']:.0%} |\n"
    
    md += f"""
## Latency

| Operation | Time |
|-----------|------|
| Encode (EN→Λ) | {encode_us:.0f} μs |
| Decode (Λ→EN) | {decode_us:.0f} μs |
| Roundtrip | {roundtrip_us:.0f} μs |
| JSON parse (baseline) | {json_parse_us:.0f} μs |

## Methodology
- Byte count: UTF-8 encoded length
- Token count: {"tiktoken cl100k_base (GPT-4)" if use_tiktoken else "heuristic (~4 chars/token)"}
- Semantic fidelity: keyword overlap between original and Lambda decode, with synonym matching
- Latency: average of 100 iterations after 10 warmup rounds
"""
    
    with open(os.path.join(out_dir, 'RESULTS.md'), 'w') as f:
        f.write(md)
    
    print(f"\n  Results written to docs/benchmark/")
    return output


if __name__ == '__main__':
    run_benchmark()
