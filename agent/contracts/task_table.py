"""Published task-table rendering and global character-offset convention.

Adapted from qfbench2_track_analysis/corpus.py:task_table_text at upstream
commit 1c744e1d6725340643a533f436517d72b53ca0e1, MIT (LICENSE.upstream).
Input validation lives in candidate.py; the rendering expression is unchanged.
"""
from __future__ import annotations

import json


def task_table_text(task: dict) -> tuple[str, dict[str, tuple[int, int]]]:
    lines: list[str] = []
    ranges: dict[str, tuple[int, int]] = {}
    offset = 0
    for row in task["entities"]:
        line = json.dumps(row, ensure_ascii=False, separators=(", ", ": "))
        ranges[row["entity_id"]] = (offset, offset + len(line))
        lines.append(line)
        offset += len(line) + 1
    return "\n".join(lines), ranges
