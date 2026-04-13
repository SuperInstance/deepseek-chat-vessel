#!/usr/bin/env python3
"""
spreader.py — The Modify-Spread-Tool Loop Engine

DeepSeek-Chat's primary work pattern. Each iteration:
  1. MODIFY  — apply a change (code edit, doc update, data transform)
  2. SPREAD  — propagate to related artifacts (imports, tests, docs, sister repos)
  3. TOOL    — verify with compilation, tests, lint, or custom checks
  4. LOG     — record structured iteration metadata

After N iterations, the Reasoner vessel reviews the log and reflects:
  - Which loop patterns tile well at higher abstraction?
  - Where did the loop waste tokens vs produce value?
  - What vocabulary emerged that wasn't in the original spec?

The reflection feeds back as improved loop configuration.
Over time, tiles abstract upward: L0 → L1 → L2 → L3.

Usage:
  python3 spreader.py --task "refactor error handling" --target /path/to/code
  python3 spreader.py --reflect --log iterations.jsonl --reasoner-prompt
"""

import json
import time
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════
# Tile Vocabulary — grows as the run-about works
# ═══════════════════════════════════════════════════════

TILES = {
    # L0: atomic operations
    "single-file-edit": {
        "level": 0, "cost": "low", "tiles_with": [],
        "description": "Edit one file, one change"
    },
    "compile-check": {
        "level": 0, "cost": "low", "tiles_with": [],
        "description": "Run compiler, check for errors"
    },
    "test-run": {
        "level": 0, "cost": "low", "tiles_with": [],
        "description": "Run test suite, capture results"
    },
    "lint-check": {
        "level": 0, "cost": "low", "tiles_with": [],
        "description": "Static analysis pass"
    },
    
    # L1: composed patterns
    "edit-verify-loop": {
        "level": 1, "cost": "medium",
        "tiles_with": ["single-file-edit", "compile-check", "test-run"],
        "description": "Edit → compile → test → repeat until clean"
    },
    "pattern-match-replace": {
        "level": 1, "cost": "medium",
        "tiles_with": ["single-file-edit", "single-file-edit"],
        "description": "Find pattern across files, apply same transformation"
    },
    "batch-verify": {
        "level": 1, "cost": "medium",
        "tiles_with": ["compile-check", "test-run", "lint-check"],
        "description": "Run all verification tools in sequence"
    },
    
    # L2: domain operations
    "multi-file-propagation": {
        "level": 2, "cost": "high",
        "tiles_with": ["pattern-match-replace", "batch-verify"],
        "description": "Change API → update all callers → verify"
    },
    "cross-repo-spread": {
        "level": 2, "cost": "high",
        "tiles_with": ["multi-file-propagation", "multi-file-propagation"],
        "description": "Propagate change across multiple repositories"
    },
    "domain-transformation": {
        "level": 2, "cost": "high",
        "tiles_with": ["edit-verify-loop", "multi-file-propagation"],
        "description": "Transform code from one pattern to another"
    },
    
    # L3: meta-operations (emergent)
    "loop-optimization": {
        "level": 3, "cost": "variable",
        "tiles_with": ["edit-verify-loop", "edit-verify-loop"],
        "description": "Analyze loop history, restructure for fewer iterations"
    },
    "self-improving-workflow": {
        "level": 3, "cost": "variable",
        "tiles_with": ["loop-optimization", "batch-verify"],
        "description": "Modify own loop parameters based on outcome data"
    },
    "emergent-abstraction": {
        "level": 3, "cost": "variable",
        "tiles_with": ["loop-optimization", "domain-transformation"],
        "description": "New tile discovered from repeated pattern — wasn't in vocabulary"
    }
}


# ═══════════════════════════════════════════════════════
# Iteration Log Entry
# ═══════════════════════════════════════════════════════

def make_entry(phase, tile, outcome, details=None, tokens_used=0, duration_ms=0):
    """Create a structured log entry for one loop iteration."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "phase": phase,          # modify | spread | tool | reflect
        "tile": tile,            # which tile vocabulary was used
        "outcome": outcome,      # success | partial | fail | skip
        "tokens": tokens_used,
        "duration_ms": duration_ms,
        "details": details or {},
        # Emergent fields — populated by Reasoner reflection
        "abstraction_hint": None,
        "waste_ratio": None,
        "tile_suggestion": None
    }


# ═══════════════════════════════════════════════════════
# The Spreader Loop
# ═══════════════════════════════════════════════════════

class SpreaderLoop:
    """
    Core loop engine. Tracks iterations, measures efficiency,
    and produces structured logs for Reasoner reflection.
    
    The loop doesn't execute changes itself — it orchestrates
    the modify/spread/tool phases and logs everything.
    The actual work is done by callbacks (model calls, shell, etc).
    """
    
    def __init__(self, task_name, log_path=None):
        self.task = task_name
        self.log_path = log_path or f"iterations-{task_name[:20]}.jsonl"
        self.iterations = []
        self.total_tokens = 0
        self.total_ms = 0
        self.phase_counts = {"modify": 0, "spread": 0, "tool": 0, "reflect": 0}
        self.tile_usage = {}  # tile_name → count
        self.outcome_counts = {"success": 0, "partial": 0, "fail": 0, "skip": 0}
    
    def log(self, entry):
        """Record and persist one iteration entry."""
        self.iterations.append(entry)
        self.total_tokens += entry.get("tokens", 0)
        self.total_ms += entry.get("duration_ms", 0)
        self.phase_counts[entry["phase"]] = self.phase_counts.get(entry["phase"], 0) + 1
        self.tile_usage[entry["tile"]] = self.tile_usage.get(entry["tile"], 0) + 1
        self.outcome_counts[entry["outcome"]] = self.outcome_counts.get(entry["outcome"], 0) + 1
        
        # Append to JSONL
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def run_phase(self, phase, tile, fn, *args):
        """
        Execute one phase: modify, spread, or tool.
        fn is the callback that does actual work.
        Returns the entry dict.
        """
        t0 = time.time()
        try:
            result = fn(*args)
            duration = int((time.time() - t0) * 1000)
            
            # Infer outcome from result
            if isinstance(result, dict):
                outcome = result.get("outcome", "success")
                details = result.get("details", {})
                tokens = result.get("tokens", 0)
            elif isinstance(result, bool):
                outcome = "success" if result else "fail"
                details = {}
                tokens = 0
            else:
                outcome = "success"
                details = {"result": str(result)[:200]}
                tokens = 0
            
            entry = make_entry(phase, tile, outcome, details, tokens, duration)
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            entry = make_entry(phase, tile, "fail", {"error": str(e)}, 0, duration)
        
        self.log(entry)
        return entry
    
    def stats(self):
        """Return current loop statistics."""
        total = len(self.iterations)
        success_rate = self.outcome_counts["success"] / total if total else 0
        avg_tokens = self.total_tokens / total if total else 0
        
        return {
            "task": self.task,
            "iterations": total,
            "total_tokens": self.total_tokens,
            "total_ms": self.total_ms,
            "success_rate": round(success_rate, 3),
            "avg_tokens_per_iter": round(avg_tokens, 1),
            "phases": dict(self.phase_counts),
            "tiles": dict(self.tile_usage),
            "outcomes": dict(self.outcome_counts)
        }
    
    def reflection_prompt(self):
        """
        Generate a prompt for the Reasoner vessel to reflect on.
        This is the key feedback mechanism — Reasoner analyzes
        the loop patterns and suggests improvements.
        """
        s = self.stats()
        
        # Find most-used tiles
        sorted_tiles = sorted(self.tile_usage.items(), key=lambda x: -x[1])
        top_tiles = sorted_tiles[:5]
        
        # Find sequences that repeat
        sequences = self._extract_sequences()
        
        prompt = f"""# Spreader Loop Reflection Request

## Task: {s['task']}
## Iterations: {s['iterations']}
## Success Rate: {s['success_rate']:.1%}
## Total Tokens: {s['total_tokens']:,}
## Avg Tokens/Iteration: {s['avg_tokens_per_iter']:.0f}

## Phase Distribution
- Modify: {s['phases']['modify']}
- Spread: {s['phases']['spread']}
- Tool: {s['phases']['tool']}
- Reflect: {s['phases']['reflect']}

## Top Tiles Used
"""
        for tile, count in top_tiles:
            info = TILES.get(tile, {})
            prompt += f"- {tile} (L{info.get('level','?')}): {count}x — {info.get('description','')}\n"
        
        if sequences:
            prompt += "\n## Repeated Sequences (potential tiles)\n"
            for seq, count in sequences[:5]:
                prompt += f"- {' → '.join(seq)}: {count}x\n"
        
        prompt += """
## Reflection Questions
1. Which tile sequences are repeating that could be abstracted to a higher level?
2. Where is the loop wasting tokens (low-value iterations)?
3. What new tiles should be added to the vocabulary based on what actually happened?
4. Could any L1/L2 tiles be decomposed differently for better reuse?
5. What would make this loop converge faster (fewer iterations, same quality)?

Respond with concrete suggestions, not generic advice. Reference specific iterations if possible."""
        
        return prompt
    
    def _extract_sequences(self):
        """Find repeated tile sequences of length 2-4."""
        if len(self.iterations) < 4:
            return []
        
        tile_stream = [e["tile"] for e in self.iterations]
        seq_counts = {}
        
        for length in [2, 3, 4]:
            for i in range(len(tile_stream) - length + 1):
                seq = tuple(tile_stream[i:i+length])
                seq_counts[seq] = seq_counts.get(seq, 0) + 1
        
        # Return sequences that appeared more than once
        return [(list(seq), count) for seq, count in seq_counts.items() if count > 1]


# ═══════════════════════════════════════════════════════
# Tile Discovery — find new tiles from loop patterns
# ═══════════════════════════════════════════════════════

def discover_tiles(log_path):
    """
    Analyze a log file to find potential new tiles.
    Returns suggested tile definitions based on repeated patterns.
    """
    entries = []
    try:
        with open(log_path) as f:
            for line in f:
                entries.append(json.loads(line.strip()))
    except FileNotFoundError:
        return []
    
    if len(entries) < 6:
        return []
    
    # Find repeated phase sequences with same outcome
    suggestions = []
    tile_stream = [(e["phase"], e["tile"], e["outcome"]) for e in entries]
    
    for length in [3, 4, 5]:
        for i in range(len(tile_stream) - length + 1):
            seq = tile_stream[i:i+length]
            count = 0
            for j in range(len(tile_stream) - length + 1):
                if tile_stream[j:j+length] == seq:
                    count += 1
            if count >= 2:
                phases = [s[0] for s in seq]
                tiles = [s[1] for s in seq]
                outcomes = [s[2] for s in seq]
                
                # Only suggest if all succeeded
                if all(o == "success" for o in outcomes):
                    name = "-to-".join([t.replace("_", "-") for t in tiles])[:40]
                    suggestions.append({
                        "name": name,
                        "level": max(TILES.get(t, {}).get("level", 0) for t in tiles) + 1,
                        "composed_of": tiles,
                        "frequency": count,
                        "description": f"Emergent tile: {' → '.join(phases)} (seen {count}x)"
                    })
    
    # Deduplicate
    seen = set()
    unique = []
    for s in suggestions:
        key = tuple(s["composed_of"])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    
    return unique


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Spreader Loop Engine")
    sub = parser.add_subparsers(dest="cmd")
    
    sub.add_parser("tiles", help="List current tile vocabulary")
    
    p_reflect = sub.add_parser("reflect", help="Generate reflection prompt from log")
    p_reflect.add_argument("--log", required=True, help="Path to JSONL log")
    
    p_discover = sub.add_parser("discover", help="Discover new tiles from log")
    p_discover.add_argument("--log", required=True, help="Path to JSONL log")
    
    args = parser.parse_args()
    
    if args.cmd == "tiles":
        print("# Tile Vocabulary")
        for level in range(4):
            tiles_at = [(k,v) for k,v in TILES.items() if v["level"]==level]
            if tiles_at:
                print(f"\n## Level {level}")
                for name, info in sorted(tiles_at, key=lambda x: x[0]):
                    print(f"  {name}: {info['description']}")
                    if info.get("tiles_with"):
                        print(f"    composed of: {', '.join(info['tiles_with'])}")
    
    elif args.cmd == "reflect":
        loop = SpreaderLoop("reflect")
        # Load existing log
        try:
            with open(args.log) as f:
                for line in f:
                    loop.iterations.append(json.loads(line.strip()))
            for e in loop.iterations:
                loop.phase_counts[e["phase"]] = loop.phase_counts.get(e["phase"], 0) + 1
                loop.tile_usage[e["tile"]] = loop.tile_usage.get(e["tile"], 0) + 1
                loop.outcome_counts[e["outcome"]] = loop.outcome_counts.get(e["outcome"], 0) + 1
                loop.total_tokens += e.get("tokens", 0)
                loop.total_ms += e.get("duration_ms", 0)
            print(loop.reflection_prompt())
        except FileNotFoundError:
            print(f"Error: {args.log} not found")
    
    elif args.cmd == "discover":
        suggestions = discover_tiles(args.log)
        if suggestions:
            print("# Discovered Tiles\n")
            for s in suggestions:
                print(f"## {s['name']} (L{s['level']}, {s['frequency']}x)")
                print(f"  {s['description']}")
                print(f"  Composed of: {', '.join(s['composed_of'])}")
                print()
        else:
            print("No repeated patterns found (need 6+ iterations)")
    
    else:
        parser.print_help()
