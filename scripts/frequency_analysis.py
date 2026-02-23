#!/usr/bin/env python3
"""
Lambda Lang v3 — Phase 1: Concept Frequency Analysis

Analyzes real agent communication to determine which concepts
are most frequent, then maps them to NSM semantic primes and
proposes a tiered atom structure.

Usage: python3 scripts/frequency_analysis.py [--sessions-dir DIR] [--limit N]
"""

import json
import os
import sys
import re
from collections import Counter
from pathlib import Path

# NSM Semantic Primes (Wierzbicka/Goddard, ~65 universals)
# These are the concepts that exist in ALL human languages.
# Agents should have them too.
NSM_PRIMES = {
    # Substantives
    "i", "you", "someone", "something", "people", "body",
    # Determiners
    "this", "the same", "other",
    # Quantifiers
    "one", "two", "some", "all", "many", "much",
    # Evaluators
    "good", "bad", "big", "small",
    # Descriptors
    "long", "short", "new", "old",
    # Mental predicates
    "think", "know", "want", "feel", "see", "hear",
    # Speech
    "say", "words", "true",
    # Actions/events
    "do", "happen", "move", "touch",
    # Existence/possession
    "exist", "have", "be",
    # Life/death
    "live", "die",
    # Time
    "when", "now", "before", "after", "a long time", "a short time", "moment",
    # Space
    "where", "here", "above", "below", "far", "near", "side", "inside",
    # Logic
    "not", "maybe", "can", "because", "if",
    # Intensifier
    "very", "more",
    # Similarity
    "like", "kind",
}

# Agent-specific concepts not in NSM but essential for machine communication
AGENT_CONCEPTS = {
    # Task lifecycle
    "task", "start", "stop", "run", "finish", "complete", "wait", "retry",
    "status", "result", "error", "success", "fail",
    # Communication
    "send", "receive", "request", "response", "acknowledge", "publish",
    "subscribe", "broadcast", "route", "message",
    # Identity/addressing
    "agent", "node", "session", "name", "id", "version",
    # State
    "state", "change", "update", "create", "delete", "read", "write",
    # Data
    "data", "config", "log", "file", "list", "count", "value", "type",
    # Control flow
    "if", "then", "else", "loop", "end",
    # Evaluation
    "check", "verify", "test", "validate", "approve", "reject",
    # Priority/urgency
    "urgent", "important", "critical", "normal", "low",
    # Relationships
    "from", "to", "about", "with", "for", "in", "at",
    # Evolution (agent-specific)
    "evolve", "mutate", "repair", "optimize", "innovate",
    "gene", "capsule", "cycle", "signal",
    # Meta
    "help", "info", "debug", "heartbeat", "health", "timeout",
}

def extract_concepts_from_text(text):
    """Extract meaningful words/concepts from text, filtering noise."""
    # Lowercase, split on non-alpha
    words = re.findall(r'[a-z]{2,}', text.lower())
    # Filter common English stopwords that carry no semantic weight
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'has', 'had', 'having', 'does', 'did', 'doing', 'will', 'would',
        'shall', 'should', 'may', 'might', 'must', 'can', 'could',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'out', 'off', 'over', 'under',
        'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'just', 'don', 'should', 'now', 'also', 'it', 'its',
        'and', 'but', 'or', 'if', 'while', 'that', 'this', 'these',
        'those', 'what', 'which', 'who', 'whom', 'up', 'about',
        'your', 'my', 'his', 'her', 'our', 'their', 'me', 'him',
        'we', 'they', 'you', 'he', 'she',
    }
    return [w for w in words if w not in stopwords and len(w) >= 2]

def load_sessions(sessions_dir, limit=200):
    """Load assistant/user messages from OpenClaw session JSONL files."""
    messages = []
    files = sorted(Path(sessions_dir).glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    
    for f in files[:limit]:
        try:
            with open(f, 'r') as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        # OpenClaw format: {"type":"message","message":{"role":"...","content":[{"type":"text","text":"..."}]}}
                        msg = obj.get('message', obj)
                        role = msg.get('role', '')
                        if role not in ('assistant', 'user'):
                            continue
                        content = msg.get('content', '')
                        if isinstance(content, str) and content:
                            messages.append(content)
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get('type') == 'text':
                                    text = part.get('text', '')
                                    if text:
                                        messages.append(text)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue
    
    return messages

def load_evolver_data(evolver_dir):
    """Load evolver events and A2A protocol data."""
    messages = []
    for fname in ['events.jsonl', 'candidates.jsonl']:
        fpath = os.path.join(evolver_dir, 'assets', 'gep', fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r') as fh:
            for line in fh:
                try:
                    obj = json.loads(line.strip())
                    messages.append(json.dumps(obj))
                except:
                    continue
    return messages

def analyze(sessions_dir, evolver_dir=None, limit=200):
    print(f"Loading sessions from {sessions_dir} (limit={limit})...")
    messages = load_sessions(sessions_dir, limit)
    print(f"  Loaded {len(messages)} messages")
    
    if evolver_dir:
        evo_msgs = load_evolver_data(evolver_dir)
        messages.extend(evo_msgs)
        print(f"  + {len(evo_msgs)} evolver messages")
    
    # Extract concepts
    all_concepts = []
    for msg in messages:
        all_concepts.extend(extract_concepts_from_text(msg))
    
    freq = Counter(all_concepts)
    total = sum(freq.values())
    print(f"\nTotal concept tokens: {total}")
    print(f"Unique concepts: {len(freq)}")
    
    # Top 200 by frequency
    top200 = freq.most_common(200)
    
    # Categorize
    print("\n" + "=" * 70)
    print("TOP 100 CONCEPTS BY FREQUENCY")
    print("=" * 70)
    print(f"{'Rank':<6}{'Concept':<20}{'Count':<10}{'%':<8}{'NSM?':<6}{'Agent?':<8}")
    print("-" * 70)
    
    cumulative = 0
    tier0_candidates = []
    
    for i, (concept, count) in enumerate(top200[:100], 1):
        pct = count / total * 100
        cumulative += pct
        is_nsm = "Y" if concept in NSM_PRIMES else ""
        is_agent = "Y" if concept in AGENT_CONCEPTS else ""
        print(f"{i:<6}{concept:<20}{count:<10}{pct:<8.2f}{is_nsm:<6}{is_agent:<8}")
        
        # Tier 0 candidates: high frequency + (NSM or Agent concept)
        if concept in NSM_PRIMES or concept in AGENT_CONCEPTS:
            tier0_candidates.append((concept, count, pct))
    
    print(f"\nTop 100 cumulative coverage: {cumulative:.1f}%")
    
    # Tier 0 proposal
    print("\n" + "=" * 70)
    print("TIER 0 CANDIDATES (NSM ∪ Agent concepts, by frequency)")
    print("=" * 70)
    tier0_candidates.sort(key=lambda x: -x[1])
    
    for i, (concept, count, pct) in enumerate(tier0_candidates[:60], 1):
        is_nsm = "NSM" if concept in NSM_PRIMES else "   "
        is_agent = "AGT" if concept in AGENT_CONCEPTS else "   "
        print(f"  {i:>3}. {concept:<20} {count:>8}  ({pct:.2f}%)  [{is_nsm}] [{is_agent}]")
    
    # Zipf analysis
    print("\n" + "=" * 70)
    print("ZIPF ANALYSIS — Encoding length recommendations")
    print("=" * 70)
    
    top50 = [c for c, _, _ in tier0_candidates[:50]]
    print(f"\n1-char atoms (top 16 verbs/entities): assign single character")
    print(f"2-char atoms (next 50): standard Lambda atoms")
    print(f"Domain atoms (rest): domain:atom prefix")
    
    # Coverage analysis
    top50_count = sum(c for _, c, _ in tier0_candidates[:50])
    print(f"\nTier 0 (50 atoms) coverage: {top50_count/total*100:.1f}% of all concept tokens")
    
    # Output JSON for next step
    output = {
        "total_tokens": total,
        "unique_concepts": len(freq),
        "tier0_candidates": [
            {"concept": c, "count": n, "pct": round(p, 3), 
             "nsm": c in NSM_PRIMES, "agent": c in AGENT_CONCEPTS}
            for c, n, p in tier0_candidates[:60]
        ],
        "top200": [{"concept": c, "count": n} for c, n in top200],
    }
    
    out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'frequency_analysis.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results written to {out_path}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sessions-dir', 
        default='/home/ubuntu/.openclaw/agents/main/sessions')
    parser.add_argument('--evolver-dir',
        default='/home/ubuntu/factory/evolver')
    parser.add_argument('--limit', type=int, default=300)
    args = parser.parse_args()
    
    analyze(args.sessions_dir, args.evolver_dir, args.limit)
