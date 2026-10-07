"""Corpus-only, offline orchestration around the frozen official stdlib baseline.

There are no learned weights, lookups, outcome files or network clients. Runtime
imports are limited to the standard library and the agent directory.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from baseline_agent.formatter import build_answer, build_entity_prediction
from baseline_agent.indexer import IndexedDoc, _doc_text
from baseline_agent.reader import predict_entity
from baseline_agent.retriever import retrieve
from contracts.task_table import task_table_text

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_CLAIM_CHARS = 160
TARGET_TYPES = {"classification", "regression", "ranking"}


class CandidateInputError(ValueError):
    """An input cannot be used safely under the published contract."""


@dataclass(frozen=True)
class ScopedDoc:
    indexed: IndexedDoc
    entity_ids: tuple[str, ...]
    shared: bool

    def admits(self, entity_id: str) -> bool:
        return self.shared or entity_id in self.entity_ids


def _bad_constant(value: str) -> None:
    raise CandidateInputError(f"Non-finite JSON constant {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CandidateInputError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def _finite_tree(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and not _is_finite_number(value):
        raise CandidateInputError("Non-finite numeric JSON value")
    if isinstance(value, dict):
        for child in value.values():
            _finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            _finite_tree(child)


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _read_json(path: Path) -> tuple[dict, bytes]:
    if path.is_symlink():
        raise CandidateInputError(f"Input file is a symlink: {path.name}")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise CandidateInputError(f"Input is not a regular file: {path.name}")
            raw = handle.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise CandidateInputError(f"Input exceeds {MAX_INPUT_BYTES} bytes: {path.name}")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_bad_constant)
    except (UnicodeError, json.JSONDecodeError, OSError) as exc:
        raise CandidateInputError(f"Unreadable UTF-8 JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise CandidateInputError(f"Input is not a JSON object: {path.name}")
    _finite_tree(value)
    return value, raw


def _calendar(value: object, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CandidateInputError(f"{field} must be YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CandidateInputError(f"{field} is not a calendar date") from exc
    return value


def is_probability_target(task: dict) -> bool:
    """Read probability units from the task, never from resolved event labels.

    The frozen credit task declares its probability output in the prompt rather
    than a machine-readable unit field. Accept that explicit point_forecast
    declaration and explicit unit fields; do not key on task/entity identifiers.
    """
    target = task.get("target", {})
    for value in (target.get("unit"), target.get("units"), task.get("prediction_unit")):
        if isinstance(value, str) and value.lower() in {"probability", "probability_0_1"}:
            return True
    prompt = task.get("prompt", "")
    if not isinstance(prompt, str):
        return False
    return bool(re.search(
        r"\bpoint_forecast\s*(?:=|:|is)\s*(?:your\s+)?(?:predicted\s+)?probability\b"
        r"|\bprobability\s+point_forecast\b", prompt, re.IGNORECASE))


def validate_task(task: dict) -> tuple[str, str, list[str] | None]:
    _finite_tree(task)
    if not isinstance(task.get("task_id"), str) or not task["task_id"].strip():
        raise CandidateInputError("task_id must be a non-empty string")
    cutoff = _calendar(task.get("cutoff_date"), "cutoff_date")
    target = task.get("target")
    if not isinstance(target, dict):
        raise CandidateInputError("target must be an object")
    target_type = task.get("target_type") or target.get("type")
    if not isinstance(target_type, str) or target_type not in TARGET_TYPES:
        raise CandidateInputError("target type must be classification/regression/ranking")
    if task.get("target_type") and target.get("type") and task["target_type"] != target["type"]:
        raise CandidateInputError("Conflicting flat/nested target types")
    labels = target.get("labels")
    if target_type == "classification":
        if (not isinstance(labels, list) or len(labels) < 2
                or any(not isinstance(x, str) or not x.strip() for x in labels)
                or len(set(labels)) != len(labels)):
            raise CandidateInputError("Classification labels must be >=2 unique non-empty strings")
    elif labels is not None:
        raise CandidateInputError("A non-classification target must not declare labels")
    entities = task.get("entities")
    if not isinstance(entities, list) or not entities:
        raise CandidateInputError("entities must be a non-empty array")
    ids: set[str] = set()
    for entity in entities:
        if not isinstance(entity, dict):
            raise CandidateInputError("An entity row must be an object")
        eid = entity.get("entity_id")
        if not isinstance(eid, str) or not eid.strip() or eid in ids:
            raise CandidateInputError("Entity IDs must be unique non-empty strings")
        ids.add(eid)
        ref = entity.get("corpus_ref", "corpus/")
        if ref != "corpus/":
            raise CandidateInputError("This candidate supports corpus_ref='corpus/' only")
        for key in ("consensus_eps", "threshold_pct"):
            if key in entity and (isinstance(entity[key], bool)
                                  or not isinstance(entity[key], (int, float))):
                raise CandidateInputError(f"{key} must be numeric")
        if entity.get("threshold_pct", 0.05) < 0:
            raise CandidateInputError("threshold_pct must be non-negative")
    return cutoff, target_type, labels


def load_corpus(corpus_dir: Path) -> list[ScopedDoc]:
    if corpus_dir.is_symlink() or not corpus_dir.is_dir():
        raise CandidateInputError("corpus must be a real directory")
    # The entrypoint accepts task and corpus only. A missing corpus index does not
    # authorize reading a parent manifest: use the task's own row as evidence.
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    manifest, _ = _read_json(manifest_path)
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise CandidateInputError("Corpus manifest must declare files[]")
    docs: list[ScopedDoc] = []
    ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise CandidateInputError("Corpus manifest entry must be an object")
        if entry.get("role") != "corpus" or entry.get("path") == "corpus/manifest.json":
            continue
        rel = entry.get("path")
        if not isinstance(rel, str) or not re.fullmatch(r"corpus/[^/\\]+\.json", rel):
            raise CandidateInputError("Corpus manifest path must be corpus/<doc_id>.json")
        name = rel[len("corpus/"):]
        doc_id = name[:-5]
        if doc_id in ids or doc_id == "task":
            raise CandidateInputError("Duplicate or reserved corpus doc_id")
        ids.add(doc_id)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CandidateInputError("Corpus manifest SHA-256 is required")
        raw_ids = entry.get("entity_ids", [])
        shared = entry.get("shared", False)
        if (not isinstance(raw_ids, list) or any(not isinstance(e, str) or not e for e in raw_ids)
                or len(set(raw_ids)) != len(raw_ids) or not isinstance(shared, bool)
                or ("shared" in entry and shared is not True) or (shared and raw_ids)):
            raise CandidateInputError("Malformed corpus entity_ids/shared labels")
        doc, raw = _read_json(corpus_dir / name)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise CandidateInputError("Corpus SHA-256 mismatch")
        if doc.get("doc_id", doc_id) != doc_id:
            raise CandidateInputError("Corpus doc_id does not match manifested filename")
        dated = _calendar(doc.get("doc_date"), "doc_date")
        spans = doc.get("spans")
        if not isinstance(doc.get("text"), str) and spans is not None:
            if not isinstance(spans, list) or any(not isinstance(s, dict)
                    or not isinstance(s.get("text", ""), str) for s in spans):
                raise CandidateInputError("Corpus spans must contain text strings")
        text = _doc_text(doc)
        if text.strip():
            docs.append(ScopedDoc(IndexedDoc(doc_id, text, dated), tuple(raw_ids), shared))
    return docs


def validate_answer(answer: dict, task: dict, docs: list[ScopedDoc]) -> None:
    cutoff, target_type, labels = validate_task(task)
    if answer.get("task_id") != task["task_id"] or answer.get("target_type") != target_type:
        raise CandidateInputError("Output task/target mismatch")
    rows = answer.get("entity_predictions")
    ids = [e["entity_id"] for e in task["entities"]]
    if not isinstance(rows, list) or [r.get("entity_id") for r in rows] != ids:
        raise CandidateInputError("Output must contain the exact ordered entity roster")
    table, ranges = task_table_text(task)
    lookup = {d.indexed.doc_id: d for d in docs}
    for row in rows:
        eid = row["entity_id"]
        if target_type == "classification" and row.get("label") not in labels:
            raise CandidateInputError("Output label outside target vocabulary")
        interval = row.get("interval", {})
        values = [row.get("point_forecast"), interval.get("level"), interval.get("lo"), interval.get("hi")]
        if any(not _is_finite_number(v) for v in values):
            raise CandidateInputError("Output prediction/interval must be finite numbers")
        if interval["level"] != 0.9 or interval["lo"] > interval["hi"]:
            raise CandidateInputError("Output requires a 90% ordered interval")
        if is_probability_target(task) and not (
                0.0 <= interval["lo"] <= row["point_forecast"] <= interval["hi"] <= 1.0):
            raise CandidateInputError("Probability point and interval must be ordered within [0,1]")
        if not isinstance(row.get("claims"), list) or not row["claims"]:
            raise CandidateInputError("Every output entity requires a claim")
        for claim in row["claims"]:
            if not isinstance(claim, dict) or "citations" in claim:
                raise CandidateInputError("Output claim shape is invalid")
            start, end = claim.get("span_start"), claim.get("span_end")
            if any(isinstance(v, bool) or not isinstance(v, int) for v in (start, end)):
                raise CandidateInputError("Citation offsets must be integer characters")
            if claim.get("doc_id") == "task":
                text = table
                lo, hi = ranges[eid]
                if not lo <= start < end <= hi:
                    raise CandidateInputError("Task citation must lie within the entity's own row")
            else:
                doc = lookup.get(claim.get("doc_id"))
                if doc is None or not doc.admits(eid) or doc.indexed.doc_date > cutoff:
                    raise CandidateInputError("Citation is unresolved/wrong-entity/post-cutoff")
                text = doc.indexed.text
            if not 0 <= start < end <= len(text) or end - start > 8000:
                raise CandidateInputError("Citation offsets are out of bounds")
            literal = claim.get("claim")
            if (not isinstance(literal, str) or not literal.strip()
                    or len(literal) > MAX_CLAIM_CHARS or literal != text[start:end]):
                raise CandidateInputError("Candidate claims must be short exact corpus/task quotes")


def run(task_path: Path, corpus_dir: Path, out_path: Path) -> dict:
    task_path, corpus_dir, out_path = Path(task_path), Path(corpus_dir), Path(out_path)
    # Input trees are frozen and may be mounted read-only. A caller cannot ask
    # this process to overwrite task, corpus or a sibling organizer input file.
    if out_path.is_symlink() or out_path.resolve().is_relative_to(task_path.parent.resolve()) \
            or out_path.resolve().is_relative_to(corpus_dir.resolve()):
        raise CandidateInputError("Output must be outside the input tree")
    task, _ = _read_json(task_path)
    cutoff, target_type, labels = validate_task(task)
    docs = load_corpus(corpus_dir)
    table, ranges = task_table_text(task)
    predictions = []
    corpus_claims = 0
    probability_target = is_probability_target(task)
    for entity in task["entities"]:
        eid = entity["entity_id"]
        eligible = [d.indexed for d in docs if d.admits(eid) and d.indexed.doc_date <= cutoff]
        query = " ".join(str(entity.get(k, "")) for k in ("name", "entity_id", "sector"))
        query += " earnings per share diluted EPS revenue"
        hit = retrieve(query, eligible, cutoff)
        if hit is not None and hit.text.strip():
            text = hit.text[:MAX_CLAIM_CHARS].rstrip()
            claim = {"doc_id": hit.doc_id, "span_start": hit.span_start,
                     "span_end": hit.span_start + len(text), "claim": text}
            span_text = hit.text
            corpus_claims += 1
        else:
            start, end = ranges[eid]
            text = table[start:min(start + MAX_CLAIM_CHARS, end)].rstrip()
            claim = {"doc_id": "task", "span_start": start,
                     "span_end": start + len(text), "claim": text}
            span_text = ""
        pred = predict_entity(entity, span_text, labels=labels)
        if probability_target:
            # An uninformed numeric band has no meaning outside a probability's
            # domain. State complete uncertainty rather than treating a past
            # EPS figure or a default zero as an event probability. At p=0.5 a
            # binary classification is tied; declared vocabulary order resolves
            # that tie deterministically, without any outcome lookup or fit.
            pred = {"label": labels[0] if labels else pred["label"],
                    "point_forecast": 0.5, "lo": 0.0, "hi": 1.0}
        predictions.append(build_entity_prediction(eid, pred["label"], pred["point_forecast"],
                                                  pred["lo"], pred["hi"], [claim]))
    answer = build_answer(task["task_id"], predictions,
        trace=f"Offline stdlib baseline; {corpus_claims} entity corpus excerpts; "
              f"{len(predictions) - corpus_claims} task-row excerpts; cutoff {cutoff}. "
              "Fallback forecasts and interval widths are uncalibrated.",
        target_type=target_type)
    answer["notes"] = {"candidate": "stdlib-development-v1", "calibration": "not_fitted",
                       "reasons": "not_submitted", "external_data": "none"}
    if probability_target:
        answer["notes"]["probability_method"] = "Uncalibrated neutral 0.5; full [0,1] interval; first-label tie break"
    validate_answer(answer, task, docs)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(answer, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    out_path.write_text(payload, encoding="utf-8")
    return answer
