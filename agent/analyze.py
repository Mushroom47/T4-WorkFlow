#!/usr/bin/env python3
"""Competition entrypoint; the container passes the leading ``analyze`` verb."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from candidate import CandidateInputError, run


def main() -> int:
    parser = argparse.ArgumentParser(description="Track 4 stdlib Development candidate")
    parser.add_argument("verb", nargs="?", default="analyze", choices=["analyze"])
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        answer = run(args.task, args.corpus, args.out)
    except (CandidateInputError, OSError) as exc:
        print(f"Candidate input/output rejected: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(answer['entity_predictions'])} entity predictions to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
