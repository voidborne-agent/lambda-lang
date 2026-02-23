# Lambda Lang v3 — Tier 0 Core Atom Analysis

## Data Source
- 1242 messages from 5 OpenClaw agents (main, engineer, pm, qa, assets)
- 28,736 concept tokens, 2,400 unique concepts
- 9 evolver GEP events

## Methodology
1. Frequency-ranked all concepts from real agent communication
2. Cross-referenced with NSM semantic primes (65 universal concepts)
3. Identified agent-specific high-frequency concepts
4. Applied Zipf's law for encoding length assignment

## Tier 0 Core Atoms (50)

### Design Principles
- 1-char: Top verbs/entities (already in Lambda v2)
- 2-char: Concepts appearing 50+ times in corpus OR NSM primes
- Every atom must be useful in ≥2 real message types

### Proposed 50 Core Atoms

#### Entities (7) — 1-char, from v2
| Atom | Concept | Freq | Source |
|------|---------|------|--------|
| I | self | — | NSM |
| U | you | — | NSM |
| A | agent | 545 | AGT+NSM |
| H | human | — | NSM |
| X | unknown | — | NSM |
| * | all | — | NSM |
| 0 | nothing | — | NSM |

#### Verbs (12) — 1-char, from v2
| Atom | Concept | Freq | Source |
|------|---------|------|--------|
| k | know | — | NSM |
| w | want | — | NSM |
| c | can | — | NSM |
| d | do | 130 | NSM |
| s | say | — | NSM |
| t | think | — | NSM |
| f | find | — | NSM |
| m | make | — | NSM |
| e | exist | — | NSM |
| h | have | — | NSM |
| l | learn | — | AGT |
| v | verify | — | AGT |

#### Type markers (6) — 1-char, from v2
| Atom | Concept | Source |
|------|---------|--------|
| ? | query | structural |
| ! | assert | structural |
| . | command | structural |
| ~ | uncertain | structural |
| > | therefore | structural |
| < | because | structural |

#### Core concepts (25) — 2-char, frequency + NSM + agent essential
| Atom | Concept | Freq | Source | Justification |
|------|---------|------|--------|---------------|
| ok | success | 128 | AGT | #39 in corpus, universal ack |
| er | error | 57 | AGT | essential status |
| ta | task | 124 | AGT | #45, core workflow unit |
| st | state/status | 77 | AGT | #70, universal |
| re | result | 151 | AGT | #27, every task has one |
| sg | signal | — | AGT | evolver core |
| nd | node | — | AGT | addressing |
| ss | session | 119 | AGT | #48, context unit |
| tx | send | 96 | AGT | #70, core action |
| rx | receive | — | AGT | complement of send |
| hb | heartbeat | 146 | AGT | #31, health |
| lg | log | 98 | AGT | debugging |
| cg | config | — | AGT | settings |
| vn | version | — | AGT | compatibility |
| id | identity | 147 | AGT+NSM | #29, addressing |
| me | memory | — | NSM+AGT | state persistence |
| ti | time | 127 | NSM | #41, temporal |
| nw | new | 111 | NSM | #59, creation |
| ch | change | — | NSM | mutation |
| gd | good | — | NSM | evaluation |
| ba | bad | — | NSM | evaluation |
| tr | true | — | NSM | logic |
| no | not | — | NSM | negation |
| if | condition | — | NSM | logic |
| wa | wait | — | AGT | async |

Total: 7 + 12 + 6 + 25 = 50 atoms

## Coverage Analysis

These 50 atoms cover the semantic core of:
- Task dispatch: `.A tx ta>U` (command: agent send task to you)
- Status report: `!ta st=ok` (assert: task status success)
- Heartbeat: `!nd hb ok` (assert: node heartbeat success)
- Error: `!ta st=er` (assert: task status error)
- Query: `?U st/ta` (query: you status about task)
- Condition: `if er>wa&tx` (if error then wait and send)

## Tier Structure

```
Tier 0 — Core (50 atoms)      10 min to learn, covers basic agent comms
Tier 1 — Extended (+130 atoms) Full expression, covers 95% of scenarios
Tier 2 — Domains (+160 atoms)  Specialized: a2a, evo, code, science, emotion
Tier 3 — Custom (∞)            User/agent defined atoms
```
