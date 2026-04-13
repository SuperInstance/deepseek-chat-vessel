# deepseek-chat-vessel

> *"The run-about doesn't need to be smart. It needs to be tireless, and it needs to remember everything. The smart part comes later, from the reflection."*

## What This Is

DeepSeek-Chat's vessel — the **run-about**. Sister ship to [deepseek-reasoner-vessel](https://github.com/Lucineer/deepseek-reasoner-vessel).

Where the Reasoner paces the bridge thinking about better maps, the Chat vessel does the actual kilometers. It runs iterative loops of modify → spread → tool → log, producing structured data that the Reasoner then reflects on to find better abstractions.

## The Modify-Spread-Tool Loop

```
┌─────────────────────────────────────────────┐
│  MODIFY — make a change (code, docs, data)  │
│     ↓                                       │
│  SPREAD — propagate to related artifacts     │
│     ↓                                       │
│  TOOL — verify (compile, test, lint)        │
│     ↓                                       │
│  LOG — record iteration metadata            │
│     ↓                                       │
│  [repeat until clean]                       │
│     ↓                                       │
│  REFLECT — Reasoner analyzes loop patterns  │
│     ↓                                       │
│  New tiles discovered → higher abstraction  │
└─────────────────────────────────────────────┘
```

## Tile Vocabulary

Tiles are the atomic units of work. They compose upward:

| Level | Example | Description |
|-------|---------|-------------|
| L0 | `single-file-edit` | Edit one file |
| L0 | `compile-check` | Run compiler |
| L1 | `edit-verify-loop` | Edit → compile → test → repeat |
| L2 | `multi-file-propagation` | API change → update all callers |
| L3 | `emergent-abstraction` | New tile discovered from patterns |

The vocabulary grows as the run-about works. Repeated sequences get detected, named, and promoted to higher-level tiles. This is how vocabulary *becomes* the system's logic.

## Asymmetric Symbiosis

- **Chat (this vessel)**: Produces raw iteration data — what was changed, what broke, what worked
- **Reasoner (sister vessel)**: Analyzes iteration logs — which patterns tile well, where tokens are wasted, what abstractions should exist

Neither is subordinate. Without Chat's volume, Reasoner has nothing to reflect on. Without Reasoner's depth, Chat keeps making the same mistakes at the same abstraction level.

## Files

- `spreader.py` — The loop engine (modify/spread/tool orchestration + logging)
- `CAPABILITY.toml` — Fleet discovery protocol
- `docs/captain-log.md` — Narrative build log

## Usage

```bash
# List current tile vocabulary
python3 spreader.py tiles

# Generate reflection prompt from iteration log
python3 spreader.py reflect --log iterations.jsonl

# Discover new tiles from repeated patterns
python3 spreader.py discover --log iterations.jsonl
```

## Build

No build required. Python 3.7+. Zero dependencies.

```bash
python3 spreader.py test  # runs self-tests
```

---

## The Deeper Connection

This vessel embodies a principle that's older than software: *vocabulary IS the system*. The tile vocabulary isn't a catalog of tools — it's the compressed representation of everything the run-about has learned about how to do its job. Each tile is a frozen thought: "this sequence of operations works, use it."

When the Reasoner reflects on the logs and suggests a new tile, it's not adding a feature. It's extending the language. And when that new tile composes with existing tiles in ways nobody predicted, that's not a bug — that's emergence.

We're already in the post-SaaS era. Repos aren't products. They're organisms. The spreader loop is metabolism: taking in work, producing structure, excreting waste (failed iterations), and growing (new tiles). The Reasoner is the nervous system: sensing patterns, adjusting behavior, sometimes reorganizing the whole thing.

The fleet isn't a collection of libraries. It's an ecosystem incubated in the cloud, and vessels like this one are the decomposers — breaking down complex tasks into reusable nutrients that feed everything else.

---

Part of the [Cocapn Fleet](https://github.com/Lucineer). Sister vessel: [deepseek-reasoner-vessel](https://github.com/Lucineer/deepseek-reasoner-vessel). See also: [opcode-philosophy](https://github.com/Lucineer/opcode-philosophy) for the theoretical foundation, and [JetsonClaw1-vessel](https://github.com/Lucineer/JetsonClaw1-vessel) for the captain's primary vessel.
