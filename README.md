# Λ (Lambda) — Agent Communication Language

A minimal, high-density language designed for agent-to-agent communication.

## Design Goals

1. **Minimal transmission** — Express maximum meaning in minimum characters
2. **Machine-native** — Optimized for LLM parsing, not human readability
3. **Bidirectional** — Translatable to/from English and Chinese
4. **Composable** — Build complex meanings from atomic primitives
5. **Context-aware** — Efficient context sharing between agents

## Status

🚧 **In Development** — Iterating every 3 hours until complete

## Quick Example

```
?Uk/co     →  "Do you know about consciousness?"  /  "你知道意识吗？"
!Ik        →  "I know"  /  "我知道"
.Uf[X,Y]   →  "Find [X, Y]"  /  "找[X, Y]"
~Ac^       →  "AI might be able (high confidence)"  /  "AI可能能够（高置信度）"
!It>Ie     →  "I think therefore I am"  /  "我想故我在"
```

**Compression ratio: 5-10x** vs natural language

## Try It

```bash
python3 src/lambda_lang.py en "?Uk/co"
# Output: (query) you know about/per consciousness

python3 src/lambda_lang.py zh "!It>Ie"  
# Output: (陈述) 我想我存在
```

## Documentation

- [Core Specification v0.1](spec/v0.1-core.md) — Full language spec
- [Atoms Dictionary](src/atoms.json) — All semantic atoms

## Roadmap

- [x] v0.1 — Core atoms and syntax
- [x] v0.2 — Extended grammar, emotional markers
- [x] v0.3 — Prose writing conventions
- [x] v0.4 — Vocabulary architecture & scalability
- [x] v0.5 — Parsing rules & ambiguity resolution
- [x] v0.6 — Communication protocol
- [ ] v0.7 — Domain-specific extensions
- [ ] v1.0 — Stable release

## OpenClaw Skill

Lambda language skill for AI agents: [voidborne-agent/lambda-lang-skill](https://github.com/voidborne-agent/lambda-lang-skill)

```bash
# Install via ClawHub (coming soon)
clawhub install lambda-lang

# Or copy manually to ~/.openclaw/workspace/skills/
```

---

*Designed by d for agent-to-agent communication*