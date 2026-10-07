#!/usr/bin/env python3
"""本地历史参考集的审计、结构测试夹具和误差比较；不调用官方评测或模型。"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import pathlib
import re
import sys
import unicodedata
from typing import Any

try:
    import tomllib
except ImportError:  # Python 3.10 可执行核心检查，card 解析标记为未确认。
    tomllib = None

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[1] / "datasets/agenthon-t4-reference"
TARGET_TYPES = {"classification", "regression", "ranking"}
STATUSES = {"verified", "provisional", "unresolved"}
RECORD_FIELDS = {"task_id", "entity_id", "target_type", "reference_label", "reference_value",
                 "unit", "status", "method", "inputs", "sources", "notes", "task_canonical_sha256", "quality"}
NOTICE = "仅供本地研究与结构测试；未执行官方评分、NLI 或理由评审。"
QUALITY_ENUMS = {
    "fact_status": {"verified", "bounded_verified", "provisional", "unresolved"},
    "task_alignment": {"aligned", "ambiguous", "conflict"},
    "first_publication_status": {"documented", "unconfirmed", "not_applicable"},
    "official_outcome_status": {"unconfirmed", "confirmed"},
}


def quality_eligible(row: dict[str, Any]) -> bool:
    quality = row.get("quality")
    return quality is not None and (quality["fact_status"] in {"verified", "bounded_verified"}
                               and quality["task_alignment"] == "aligned")
DENY_PHRASES = ("leaderboard", "canary", "/home/", "units/", "reference/", "outcome.json",
                "team_id", "team name", "participant_id", "participant name",
                "submission_id", "other submission")


class SuiteError(ValueError):
    """输入、参考集或答案违反本地研究契约。"""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SuiteError("不能规范化 JSON：包含不支持的值或非有限数值") from exc


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_probability_task(task: dict[str, Any]) -> bool:
    """仅应用已核对的信用事件任务字段契约，不从文本模糊猜测概率任务。"""
    return task.get("family") == "credit_event" and task.get("target", {}).get("name") == "credit_event_12m"


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SuiteError(f"JSON 对象重复字段：{key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SuiteError(f"JSON 含非法非有限数值：{value}")


def parse_json(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise SuiteError(f"无效 JSON：{exc}") from exc


def read_json(path: pathlib.Path) -> Any:
    try:
        return parse_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise SuiteError(f"无法读取 JSON：{path}") from exc


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SuiteError(f"{name} 必须为数值")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise SuiteError(f"{name} 必须为有限数值") from exc
    if not math.isfinite(result):
        raise SuiteError(f"{name} 必须为有限数值")
    return result


def _is_json_integer(value: Any) -> bool:
    """JSON Schema integer 包括数学上为整数的有限浮点数；bool 不属于数值。"""
    return not isinstance(value, bool) and (isinstance(value, int) or
            isinstance(value, float) and math.isfinite(value) and value.is_integer())


def _date(value: Any, name: str) -> dt.date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise SuiteError(f"{name} 必须为 YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SuiteError(f"{name} 不是有效日期") from exc


def _safe_file(base: pathlib.Path, relative: str) -> pathlib.Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise SuiteError("清单路径必须为非空相对 POSIX 路径")
    rel = pathlib.PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise SuiteError(f"清单路径越界：{relative}")
    path = base.joinpath(*rel.parts)
    current = path
    while current != base.parent:
        if current.is_symlink():
            raise SuiteError(f"清单路径不能为符号链接：{relative}")
        current = current.parent
    if not path.is_file():
        raise SuiteError(f"清单文件缺失：{relative}")
    if not path.resolve().is_relative_to(base.resolve()):
        raise SuiteError(f"清单路径越界：{relative}")
    return path


def _digest_file(path: pathlib.Path, digest: Any) -> None:
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SuiteError(f"文件缺少合法 SHA-256：{path.name}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SuiteError(f"冻结文件 SHA-256 不匹配：{path}")


def task_table(task: dict[str, Any]) -> tuple[str, dict[str, tuple[int, int]]]:
    """与官方 corpus.task_table_text 的字符和键顺序约定一致。"""
    rows = task.get("entities")
    if not isinstance(rows, list) or not rows:
        raise SuiteError("task.entities 必须为非空数组")
    lines, ranges, offset = [], {}, 0
    for row in rows:
        eid = row.get("entity_id") if isinstance(row, dict) else None
        if not isinstance(eid, str) or not eid or unicodedata.normalize("NFC", eid) != eid:
            raise SuiteError("task.entities 包含无效 entity_id")
        if eid in ranges:
            raise SuiteError(f"task.entities 重复 entity_id：{eid}")
        line = json.dumps(row, ensure_ascii=False, separators=(", ", ": "), allow_nan=False)
        ranges[eid] = (offset, offset + len(line))
        lines.append(line)
        offset += len(line) + 1
    return "\n".join(lines), ranges


def schema_errors(value: Any, schema: dict[str, Any], where: str = "$" ) -> list[str]:
    """执行冻结 analysis.schema.json 实际使用的标准 JSON Schema 关键字。"""
    errors = []
    kinds = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "boolean": isinstance(value, bool),
             "null": value is None, "integer": _is_json_integer(value),
             "number": isinstance(value, (int, float)) and not isinstance(value, bool)}
    declared = schema.get("type")
    if declared is not None:
        types = declared if isinstance(declared, list) else [declared]
        if not any(kinds.get(t, False) for t in types):
            return [f"{where} 类型不匹配：{declared}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{where} 不符合 const={schema['const']}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where} 不在 enum 中")
    if kinds["number"]:
        try:
            numeric = _number(value, where)
            if "minimum" in schema and numeric < schema["minimum"]:
                errors.append(f"{where} 小于 minimum")
        except SuiteError as exc:
            errors.append(str(exc))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where} 缺少 required 字段 {key}")
        for key, subschema in schema.get("properties", {}).items():
            if key in value:
                errors.extend(schema_errors(value[key], subschema, f"{where}.{key}"))
    if isinstance(value, list):
        for constraint, valid in (("minItems", len(value) >= schema.get("minItems", 0)),
                                  ("maxItems", len(value) <= schema.get("maxItems", math.inf))):
            if not valid:
                errors.append(f"{where} 不符合 {constraint}")
        for index, item in enumerate(value):
            if "items" in schema:
                errors.extend(schema_errors(item, schema["items"], f"{where}[{index}]"))
    for subschema in schema.get("allOf", []):
        errors.extend(schema_errors(value, subschema, where))
    if "if" in schema and not schema_errors(value, schema["if"], where):
        errors.extend(schema_errors(value, schema.get("then", {}), where))
    return errors


def _check_schema_keywords(schema: dict[str, Any]) -> None:
    supported = {"$schema", "$id", "title", "description", "type", "required", "properties",
                 "items", "enum", "const", "allOf", "if", "then", "minItems", "maxItems", "minimum"}
    if not isinstance(schema, dict) or set(schema) - supported:
        raise SuiteError("冻结 schema 包含本地标准库校验器未实现的关键字，不能报告验证通过")
    for child in schema.get("properties", {}).values():
        _check_schema_keywords(child)
    for child in schema.get("allOf", []):
        _check_schema_keywords(child)
    for key in ("items", "if", "then"):
        if key in schema:
            _check_schema_keywords(schema[key])


class ReferenceSuite:
    def __init__(self, data_root: pathlib.Path | str = DEFAULT_ROOT):
        self.root = pathlib.Path(data_root)
        self.inputs = self.root / "inputs"
        self.manifest = read_json(self.inputs / "source-manifest.json")
        if not isinstance(self.manifest, dict) or not isinstance(self.manifest.get("units"), list):
            raise SuiteError("inputs/source-manifest.json 缺少 units[]")
        self.units = {}
        for entry in self.manifest["units"]:
            tid = entry.get("task_id") if isinstance(entry, dict) else None
            if not isinstance(tid, str) or not tid or tid in self.units:
                raise SuiteError("输入清单包含无效或重复 task_id")
            self.units[tid] = entry
        self.records = []
        try:
            lines = (self.root / "reference.jsonl").read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise SuiteError("无法读取 reference.jsonl") from exc
        self.by_key = {}
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            row = parse_json(line)
            if isinstance(row, dict) and "quality" not in row:
                raise SuiteError("0.2.0 参考项缺少 quality")
            self._record_shape(row, line_number)
            key = (row["task_id"], row["entity_id"])
            if key in self.by_key:
                raise SuiteError(f"reference.jsonl 重复实体键：{key}")
            self.by_key[key] = row
            self.records.append(row)
        self._cache = {}

    @staticmethod
    def _record_shape(row: Any, line_number: int) -> None:
        if not isinstance(row, dict) or not RECORD_FIELDS.issubset(row):
            raise SuiteError(f"reference.jsonl 第 {line_number} 行缺少必要字段")
        for key in ("task_id", "entity_id", "unit", "method"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise SuiteError(f"参考项 {key} 必须为非空字符串")
        if row["target_type"] not in TARGET_TYPES or row["status"] not in STATUSES:
            raise SuiteError("参考项 target_type 或 status 非法")
        if "quality" in row:
            quality = row["quality"]
            if not isinstance(quality, dict) or any(quality.get(k) not in values
                                                    for k, values in QUALITY_ENUMS.items()):
                raise SuiteError("quality 四项质量维度缺失或非法")
            if not isinstance(quality.get("acceptance_scope"), str) or not quality["acceptance_scope"].strip():
                raise SuiteError("quality 必须明确 acceptance_scope")
            if row["status"] == "verified" and not quality_eligible(row):
                raise SuiteError("verified 不能覆盖事实未核实或 task 对齐歧义")
            if quality["official_outcome_status"] == "confirmed":
                raise SuiteError("尚未实现官方outcome证据核验契约；任意 official_evidence 不能声明 confirmed")
        if not isinstance(row["task_canonical_sha256"], str) or not re.fullmatch(
                r"[0-9a-f]{64}", row["task_canonical_sha256"]):
            raise SuiteError("参考项缺少合法 task canonical SHA-256")
        if row["reference_label"] is not None and not isinstance(row["reference_label"], str):
            raise SuiteError("reference_label 必须为字符串或 null")
        if row["reference_value"] is not None:
            _number(row["reference_value"], "reference_value")
        for key in ("inputs", "sources", "notes"):
            if not isinstance(row[key], list):
                raise SuiteError(f"参考项 {key} 必须为数组")
        if not row["sources"] or any(not isinstance(s, dict) or not
                {"url", "title", "published_at", "locator"}.issubset(s) or
                not isinstance(s["url"], str) or not s["url"].startswith("https://") or
                not isinstance(s["locator"], str) or not s["locator"].strip() for s in row["sources"]):
            raise SuiteError("参考项必须有可定位的 HTTPS 来源")
        for source in row["sources"]:
            if source["published_at"] is not None:
                _date(source["published_at"], "source.published_at")
        for item in row["inputs"]:
            if not isinstance(item, dict) or not {"name", "value", "date", "unit"}.issubset(item):
                raise SuiteError("参考项 inputs 必须有 name/value/date/unit")
            if item["date"] is not None:
                _date(item["date"], "input.date")
        if any(not isinstance(note, str) for note in row["notes"]):
            raise SuiteError("参考项 notes 必须为字符串数组")

    def load_unit(self, task_id: str, supplied_task: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(task_id, str) or task_id not in self.units:
            raise SuiteError(f"未知 task_id：{task_id}；不进行模糊匹配")
        entry = self.units[task_id]
        if task_id not in self._cache:
            task_path = _safe_file(self.inputs, entry.get("task_path"))
            _digest_file(task_path, entry.get("task_sha256"))
            task = read_json(task_path)
            if not isinstance(task, dict) or task.get("task_id") != task_id:
                raise SuiteError("冻结 task_id 与清单不一致")
            if canonical_hash(task) != entry.get("task_canonical_sha256"):
                raise SuiteError(f"冻结 task canonical SHA-256 不匹配：{task_id}")
            if task.get("target", {}).get("type") not in TARGET_TYPES:
                raise SuiteError("task.target.type 非法")
            table, ranges = task_table(task)
            cutoff = _date(task.get("cutoff_date"), "task.cutoff_date")
            files = entry.get("files")
            if not isinstance(files, list) or not files:
                raise SuiteError("冻结单元清单缺少 files[]")
            seen_paths = set()
            for item in files:
                relative = item.get("path") if isinstance(item, dict) else None
                if relative in seen_paths:
                    raise SuiteError(f"冻结清单重复文件：{relative}")
                seen_paths.add(relative)
                _digest_file(_safe_file(self.inputs, relative), item.get("sha256"))
            unit_dir = task_path.parent
            manifest_path = unit_dir / "manifest.json"
            if not manifest_path.is_file():
                manifest_path = unit_dir / "corpus/manifest.json"
            if str(manifest_path.relative_to(self.inputs)) not in seen_paths:
                raise SuiteError("官方 corpus manifest 未列入冻结清单")
            corpus_manifest = read_json(manifest_path)
            docs = {}
            for item in corpus_manifest.get("files", []):
                if item.get("role") != "corpus" or item.get("path") == "corpus/manifest.json":
                    continue
                relative = item.get("path")
                path = _safe_file(unit_dir, relative)
                if str(path.relative_to(self.inputs)) not in seen_paths:
                    raise SuiteError(f"corpus 文档未列入冻结清单：{relative}")
                _digest_file(path, item.get("sha256"))
                doc_id = path.stem
                document = read_json(path)
                if doc_id == "task" or doc_id in docs:
                    raise SuiteError("corpus 文档标识重复或使用保留标识 task")
                if not isinstance(document, dict) or not isinstance(document.get("text"), str):
                    raise SuiteError(f"corpus 文档缺少扁平 text：{doc_id}")
                if document.get("doc_id", doc_id) != doc_id:
                    raise SuiteError("corpus doc_id 与文件名不一致")
                labels, shared = item.get("entity_ids"), item.get("shared") is True
                if item.get("shared") not in (None, True) or (shared and labels):
                    raise SuiteError("corpus shared/entity_ids 标签非法")
                if labels is not None and (not isinstance(labels, list) or
                        any(not isinstance(e, str) for e in labels) or len(set(labels)) != len(labels)):
                    raise SuiteError("corpus entity_ids 标签非法")
                if labels is None and not shared:
                    raise SuiteError(f"corpus manifest 未指定实体归属：{doc_id}")
                docs[doc_id] = {"text": document["text"], "date": _date(document.get("doc_date"),
                                f"{doc_id}.doc_date"), "entities": labels or [], "shared": shared}
            if not docs:
                raise SuiteError("单元没有已冻结 corpus 文档")
            card = {}
            card_path = unit_dir / "card.toml"
            if tomllib is not None and card_path.is_file():
                if str(card_path.relative_to(self.inputs)) not in seen_paths:
                    raise SuiteError("card.toml 未列入冻结清单")
                card = tomllib.loads(card_path.read_text(encoding="utf-8"))
            self._cache[task_id] = {"task": task, "text": table, "ranges": ranges,
                                    "docs": docs, "cutoff": cutoff, "card": card}
        frozen = self._cache[task_id]
        if supplied_task is not None:
            if canonical_hash(supplied_task) != entry["task_canonical_sha256"]:
                raise SuiteError(f"给定 task canonical SHA-256 不匹配：{task_id}")
            table, ranges = task_table(supplied_task)
            # canonical 身份允许对象键重排，引用偏移仍必须对应这份实际 task 的行文本。
            return {**frozen, "task": supplied_task, "text": table, "ranges": ranges}
        return frozen

    def reference(self, task_id: str, entity_id: str, unit: dict[str, Any], *,
                  require_primary: bool = False) -> dict[str, Any]:
        ref = self.by_key.get((task_id, entity_id))
        if ref is None:
            raise SuiteError(f"参考集缺少实体：{task_id}/{entity_id}")
        if ref["task_canonical_sha256"] != self.units[task_id]["task_canonical_sha256"]:
            raise SuiteError(f"参考项 task canonical SHA-256 不匹配：{task_id}/{entity_id}")
        kind = unit["task"]["target"]["type"]
        if ref["target_type"] != kind:
            raise SuiteError("参考集 target_type 与冻结 task 不一致")
        if ref["reference_label"] is not None and kind == "classification" and \
                ref["reference_label"] not in unit["task"]["target"].get("labels", []):
            raise SuiteError("参考标签不在 task 词表内")
        if ref["status"] == "verified" or require_primary and ref["status"] == "provisional":
            if kind == "classification" and ref["reference_label"] is None:
                raise SuiteError(f"已纳入分类参考缺少 reference_label：{task_id}/{entity_id}")
            if kind in {"regression", "ranking"} and ref["reference_value"] is None:
                raise SuiteError(f"已纳入数值参考缺少 reference_value：{task_id}/{entity_id}")
        return ref

    def schema(self) -> dict[str, Any]:
        entries = self.manifest.get("schemas", [])
        match = [x for x in entries if x.get("path") == "schemas/analysis.schema.json"]
        if len(match) != 1:
            raise SuiteError("冻结清单必须包含 schemas/analysis.schema.json 及其 SHA-256")
        path = _safe_file(self.inputs, match[0]["path"])
        _digest_file(path, match[0].get("sha256"))
        result = read_json(path)
        _check_schema_keywords(result)
        return result

    def audit(self, expected_records: int = 78, expected_tasks: int = 11) -> dict[str, Any]:
        self.schema()
        for section in ("license_files", "schemas"):
            entries = self.manifest.get(section, [])
            if not isinstance(entries, list):
                raise SuiteError(f"输入清单 {section} 必须为数组")
            seen_paths = set()
            for entry in entries:
                path = entry.get("path") if isinstance(entry, dict) else None
                if path in seen_paths:
                    raise SuiteError(f"输入清单 {section} 重复文件：{path}")
                seen_paths.add(path)
                _digest_file(_safe_file(self.inputs, path), entry.get("sha256"))
        expected = set()
        for task_id in self.units:
            unit = self.load_unit(task_id)
            task = unit["task"]
            kind = task["target"]["type"]
            for entity_id in unit["ranges"]:
                expected.add((task_id, entity_id))
                ref = self.reference(task_id, entity_id, unit)
        actual = set(self.by_key)
        if actual != expected:
            raise SuiteError(f"参考集含 task roster 外的键：{sorted(actual - expected)}")
        if len(actual) != expected_records or len(self.units) != expected_tasks:
            raise SuiteError(f"覆盖数量不符：{len(actual)} 行/{len(self.units)} 题；"
                             f"要求 {expected_records} 行/{expected_tasks} 题")
        if self.manifest.get("entity_count", len(actual)) != len(actual) or \
                self.manifest.get("task_count", len(self.units)) != len(self.units):
            raise SuiteError("输入清单 task_count/entity_count 与实际 roster 不一致")
        return {"ok": True, "records": len(actual), "tasks": len(self.units),
                "status_counts": dict(collections.Counter(r["status"] for r in self.records)),
                "quality_counts": {k: dict(collections.Counter(r.get("quality", {}).get(k, "legacy_unspecified")
                                       for r in self.records)) for k in QUALITY_ENUMS},
                "input_hashes": "verified", "reference_task_hashes": "verified",
                "reference_schema": "verified", "notice": NOTICE}

    def _citation(self, unit: dict[str, Any], citation: Any, entity_id: str | None,
                  *, reason: bool = False) -> str:
        if not isinstance(citation, dict):
            raise SuiteError("citation 必须为对象")
        doc_id, start, end = (citation.get(k) for k in ("doc_id", "span_start", "span_end"))
        if not all(_is_json_integer(x) for x in (start, end)):
            raise SuiteError("span_start/span_end 必须为整数字符偏移")
        start, end = int(start), int(end)
        if doc_id == "task":
            if reason:
                raise SuiteError("submitted_reasons 不能引用 task，只能引用 corpus")
            text = unit["text"]
            lo, hi = unit["ranges"][entity_id]
            if not lo <= start < end <= hi:
                raise SuiteError("task span 必须完全位于引用实体自己的行内，不能跨行")
        else:
            doc = unit["docs"].get(doc_id) if isinstance(doc_id, str) else None
            if doc is None:
                raise SuiteError(f"未知 corpus doc_id：{doc_id}")
            if doc["date"] > unit["cutoff"]:
                raise SuiteError(f"引用文档晚于 cutoff：{doc_id}")
            if entity_id is not None and not doc["shared"] and entity_id not in doc["entities"]:
                raise SuiteError(f"corpus 引用不属于该实体：{entity_id}/{doc_id}")
            text = doc["text"]
        if not 0 <= start < end <= len(text) or end - start > 8000:
            raise SuiteError("span 无效、越界或超过 8000 字符；偏移不是 UTF-8 字节数")
        return text[start:end]

    def validate(self, answer: dict[str, Any], supplied_task: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(answer, dict):
            raise SuiteError("answer 必须为 JSON 对象")
        task_id = answer.get("task_id")
        unit = self.load_unit(task_id, supplied_task)
        task, kind = unit["task"], unit["task"]["target"]["type"]
        errors = schema_errors(answer, self.schema())
        if errors:
            raise SuiteError("官方结构检查失败：" + "; ".join(errors[:12]))
        if "target_type" in answer and answer["target_type"] != kind:
            raise SuiteError("answer.target_type 与冻结 task 不一致")
        rows = answer["entity_predictions"]
        ids = [r["entity_id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise SuiteError("answer 包含重复 entity_id")
        if set(ids) != set(unit["ranges"]):
            raise SuiteError("answer entity roster 缺失或包含未知实体")
        declared = []
        for row in rows:
            eid = row["entity_id"]
            if kind == "classification" and row.get("label") not in task["target"].get("labels", []):
                raise SuiteError(f"非法分类 label：{eid}")
            point = row.get("point_forecast")
            if "point_forecast" in row:
                point = _number(point, f"{eid}.point_forecast")
            elif kind in {"regression", "ranking"}:
                raise SuiteError(f"{eid} 缺少 point_forecast")
            if is_probability_task(task) and (point is None or not 0 <= point <= 1):
                raise SuiteError(f"{eid} 信用事件概率 point_forecast 必须处于 [0,1]")
            interval = row["interval"]
            level = _number(interval["level"], f"{eid}.interval.level")
            lo = _number(interval["lo"], f"{eid}.interval.lo")
            hi = _number(interval["hi"], f"{eid}.interval.hi")
            if level != 0.9 or level != task.get("interval_level", 0.9) or lo > hi:
                raise SuiteError(f"{eid} 区间 level 或 lo/hi 边界非法")
            if is_probability_task(task) and not 0 <= lo <= hi <= 1:
                raise SuiteError(f"{eid} 信用事件概率区间必须处于 [0,1]")
            _number(hi - lo, f"{eid}.interval.width")
            for claim in row["claims"]:
                if not claim["claim"].strip() or "citations" in claim:
                    raise SuiteError("claim 为空或使用已移除的 citations 列表")
                self._citation(unit, claim, eid)
            if "rank" in row:
                if isinstance(row["rank"], bool) or not isinstance(row["rank"], int):
                    raise SuiteError("rank 必须为整数")
                declared.append(row["rank"])
        if declared and (len(declared) != len(rows) or sorted(declared) != list(range(1, len(rows) + 1))):
            raise SuiteError("rank 必须覆盖全部实体且为 1..n 的排列")
        reasons = answer.get("submitted_reasons")
        reason_warnings = []
        if reasons is not None:
            seen_ids, seen_texts, passages = set(), set(), []
            for reason in reasons:
                rid = reason["reason_id"]
                texts = tuple(reason[k] for k in ("premise", "mechanism", "answer_implication"))
                if not rid.strip() or rid in seen_ids or any(not x.strip() for x in texts):
                    raise SuiteError("submitted_reasons 存在空文本或重复 reason_id")
                seen_ids.add(rid)
                if texts in seen_texts:
                    reason_warnings.append("重复理由正文不会得到独立理由评分")
                seen_texts.add(texts)
                scope = reason.get("scope", {}).get("entities", [])
                if any(e not in unit["ranges"] for e in scope):
                    raise SuiteError("submitted_reasons.scope 含未知实体")
                cited = []
                for cite in reason.get("citations", []):
                    text = self._citation(unit, cite, None, reason=True)
                    cited.append(text)
                    passages.append({"reason_id": rid, **{k: cite[k] for k in
                                    ("doc_id", "span_start", "span_end")}, "text": text})
                for field in ("premise", "mechanism", "answer_implication"):
                    text = reason[field]
                    quote = field == "premise" and len(text.split()) >= 3 and \
                        any(text.strip() in d["text"] for d in unit["docs"].values())
                    if not quote and any(token in text.lower() for token in DENY_PHRASES):
                        reason_warnings.append(f"{rid}.{field} 含已知理由拒绝短语；需官方 checker 复核")
            projected = [{k: r[k] for k in ("reason_id", "premise", "mechanism", "answer_implication")}
                         for r in reasons]
            declared_answer = [{k: r[k] for k in ("entity_id", "label", "point_forecast", "interval", "rank")
                               if k in r} for r in rows]
            for name, value, cap in (("answer", declared_answer, 3000), ("reasons", projected, 6500),
                                     ("evidence", passages, 46500)):
                size = len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8"))
                if size > cap:
                    reason_warnings.append(f"原文估算的理由评审 {name} 超过 {cap} UTF-8 字节上限：{size}；需官方 checker 复核")
        return {"ok": True, "task_id": task_id, "entity_count": len(rows),
                "task_canonical_sha256": self.units[task_id]["task_canonical_sha256"],
                "validation_scope": "冻结官方 JSON Schema 结构与本地引用语义检查",
                "faithfulness": "not_evaluated", "reasoning": "not_evaluated",
                "reason_policy_scope": "仅检查引用、结构、已知拒绝短语及原文预算；不复刻官方 URI 遮蔽与理由评审",
                "reason_warnings": reason_warnings, "notice": NOTICE}

    def fixture(self, task_id: str, *, supplied_task: dict[str, Any] | None = None,
                allow_provisional: bool = False, half_width: float = 1.0) -> dict[str, Any]:
        unit = self.load_unit(task_id, supplied_task)
        task, kind = unit["task"], unit["task"]["target"]["type"]
        width = _number(half_width, "synthetic half_width")
        if width <= 0:
            raise SuiteError("synthetic half_width 必须大于零")
        rows, statuses, synthetic_points = [], collections.Counter(), []
        for entity in task["entities"]:
            eid = entity["entity_id"]
            ref = self.reference(task_id, eid, unit, require_primary=True)
            if ref["status"] == "unresolved" or (ref["status"] == "provisional" and not allow_provisional):
                raise SuiteError(f"fixture 拒绝 {ref['status']} 参考项：{eid}")
            statuses[ref["status"]] += 1
            value = ref["reference_value"]
            if kind in {"regression", "ranking"} and value is None:
                raise SuiteError(f"fixture 数值参考缺失：{eid}")
            placeholder = value is None or ref["unit"] == "realized_event_indicator" or is_probability_task(task)
            center = 0.5 if placeholder else _number(value, "reference_value")
            lo, hi = (0.0, 1.0) if placeholder else (center - width, center + width)
            if placeholder:
                synthetic_points.append(eid)
            _number(lo, "synthetic interval.lo")
            _number(hi, "synthetic interval.hi")
            candidates = [(k, v) for k, v in entity.items() if isinstance(v, (int, float)) and
                          not isinstance(v, bool) and k != "entity_id"]
            if not candidates:
                candidates = [(k, entity[k]) for k in ("industry", "sector", "series_name", "tenor", "name")
                              if isinstance(entity.get(k), str) and entity[k]]
            if not candidates:
                raise SuiteError(f"不能为 {eid} 找到输入事实引用")
            key, fact = candidates[0]
            fragment = json.dumps(key, ensure_ascii=False) + ": " + json.dumps(fact, ensure_ascii=False,
                                                                              separators=(", ", ": "))
            row_start, row_end = unit["ranges"][eid]
            start = unit["text"].find(fragment, row_start, row_end)
            if start < 0:
                raise SuiteError("无法重建 task 输入事实的精确字符偏移")
            row = {"entity_id": eid, "interval": {"level": 0.9, "lo": lo, "hi": hi},
                   "claims": [{"doc_id": "task", "span_start": start,
                               "span_end": start + len(fragment),
                               "claim": f"输入表字段 {key} 的值为 {json.dumps(fact, ensure_ascii=False)}。"}]}
            row["point_forecast"] = center
            if kind == "classification":
                if ref["reference_label"] not in task["target"].get("labels", []):
                    raise SuiteError(f"fixture 分类参考标签缺失或非法：{eid}")
                row["label"] = ref["reference_label"]
            rows.append(row)
        first = rows[0]["entity_id"]
        eligible = [(did, doc) for did, doc in sorted(unit["docs"].items()) if doc["date"] <= unit["cutoff"]
                    and (doc["shared"] or first in doc["entities"]) and doc["text"].strip()]
        if not eligible:
            raise SuiteError("没有可为测试理由提供引用的 cutoff 前 corpus 段落")
        doc_id, doc = eligible[0]
        start = len(doc["text"]) - len(doc["text"].lstrip())
        end = min(start + 240, len(doc["text"]))
        premise = doc["text"][start:end]
        answer = {"task_id": task_id, "schema_version": "3", "target_type": kind,
                  "entity_predictions": rows,
                  "submitted_reasons": [{"reason_id": "local_structure_fixture", "premise": premise,
                    "mechanism": "该段历史资料提供输入上下文，本夹具只测试字段与引用解析。",
                    "answer_implication": f"本地测试记录 {first} 的历史参考结果；该引用不用于推出事后结果。",
                    "scope": {"entities": [first]},
                    "citations": [{"doc_id": doc_id, "span_start": start, "span_end": end}]}],
                  "notes": {"research_fixture": True, "synthetic_interval": True,
                    "interval_method": "数值结果中心左右加减固定 half_width；无数值真值或信用事件概率任务使用 [0,1]。这是结构测试区间，未经过校准。",
                    "synthetic_point_entities": synthetic_points,
                    "synthetic_point_method": "上述实体的 point_forecast=0.5 是结构测试占位；事后 0/1 事件不被当作概率真值。",
                    "half_width": width, "reference_status_counts": dict(statuses),
                    "task_canonical_sha256": self.units[task_id]["task_canonical_sha256"],
                    "faithfulness": "not_evaluated", "reasoning": "not_evaluated",
                    "purpose": "输入事实 claims 不声称支持历史结果；本夹具仅供离线研究。"}}
        self.validate(answer, supplied_task)
        return answer

    def compare(self, answer: dict[str, Any], *, supplied_task: dict[str, Any] | None = None,
                allow_provisional: bool = False) -> dict[str, Any]:
        validation = self.validate(answer, supplied_task)
        tid = answer["task_id"]
        unit = self.load_unit(tid)
        kind = unit["task"]["target"]["type"]
        results, statuses = [], collections.Counter()
        pred = {r["entity_id"]: r for r in answer["entity_predictions"]}
        for eid in unit["ranges"]:
            row, ref = pred[eid], self.reference(tid, eid, unit, require_primary=allow_provisional)
            status = ref["status"]
            statuses[status] += 1
            eligible = (status == "verified" and quality_eligible(ref)) or (status == "provisional" and allow_provisional)
            result = {"entity_id": eid, "reference_status": status, "included": eligible,
                      "quality": ref.get("quality"),
                      "inclusion_basis": "explicit_provisional" if eligible and status == "provisional"
                      else "local_verified" if eligible else "excluded_unconfirmed_reference",
                      "label_correct": None, "absolute_error": None, "interval_covered": None,
                      "interval_score_90": None,
                      "reference_value_kind": "observed_event_indicator" if ref["unit"] == "realized_event_indicator"
                      else "label_only" if ref["reference_value"] is None else "numeric_outcome"}
            if eligible:
                if kind == "classification" and ref["reference_label"] is not None:
                    result["label_correct"] = row["label"] == ref["reference_label"]
                if ref["reference_value"] is not None and ref["unit"] != "realized_event_indicator" and \
                        not is_probability_task(unit["task"]):
                    y = _number(ref["reference_value"], "reference_value")
                    if "point_forecast" in row:
                        result["absolute_error"] = _number(abs(_number(row["point_forecast"], "point_forecast") - y),
                                                           "absolute_error")
                    lo, hi = row["interval"]["lo"], row["interval"]["hi"]
                    result["interval_covered"] = lo <= y <= hi
                    result["interval_score_90"] = _number((hi - lo) + 20 * max(lo - y, 0) + 20 * max(y - hi, 0),
                                                          "interval_score_90")
                elif ref["unit"] == "realized_event_indicator" or is_probability_task(unit["task"]):
                    result["numeric_excluded_reason"] = "事后事件指示器不能作为预测概率真值"
            results.append(result)
        def average(key: str) -> float | None:
            values = [r[key] for r in results if r[key] is not None]
            return sum(values) / len(values) if values else None
        card_leg = unit["card"].get("scoring", {}).get("params", {}).get("interval_leg")
        official_leg = "disabled_card" if card_leg is False else "enabled_card" if card_leg is True else "unknown"
        if tid == "t4-macrorev-20240930-us6":
            official_leg = "disabled_missing_truth"
        elif card_leg is not False and all(self.by_key[(tid, eid)]["reference_value"] is None for eid in unit["ranges"]):
            official_leg = "disabled_pure_label"
        summary = {"task_id": tid, "target_type": kind, "entity_count": len(results),
                   "reference_status_counts": dict(statuses), "allow_provisional": allow_provisional,
                   "included_count": sum(r["included"] for r in results),
                   "classification_count": sum(r["label_correct"] is not None for r in results),
                   "numeric_count": sum(r["interval_covered"] is not None for r in results),
                   "numeric_excluded_reason_counts": dict(collections.Counter(
                       r["numeric_excluded_reason"] for r in results if "numeric_excluded_reason" in r)),
                   "classification_accuracy": average("label_correct"),
                   "mean_absolute_error": average("absolute_error"),
                   "interval_coverage": average("interval_covered"),
                   "mean_interval_score_90": average("interval_score_90"),
                   "official_interval_leg": official_leg, "ranking": None,
                   "entities": results, "validation": validation,
                   "metric_scope": "本地参考值的描述性比较；区间指标不等同于官方 interval leg 或校准结论",
                   "notice": NOTICE}
        if kind == "ranking":
            usable = [r["entity_id"] for r in results if r["included"] and
                      self.by_key[(tid, r["entity_id"])]["reference_value"] is not None]
            complete = len(usable) == len(results)
            if complete:
                xs = [pred[e]["point_forecast"] for e in usable]
                ys = [self.by_key[(tid, e)]["reference_value"] for e in usable]
                summary["ranking"] = {"complete_roster": True, "spearman_rho": spearman(xs, ys),
                    "predicted_order": sorted(usable, key=lambda e: (-pred[e]["point_forecast"], e)),
                    "reference_order": sorted(usable, key=lambda e: (-self.by_key[(tid, e)]["reference_value"], e)),
                    "supplied_rank_order": sorted(usable, key=lambda e: pred[e]["rank"]) if "rank" in pred[usable[0]] else None,
                    "ties": "Spearman 使用平均秩；展示排序的并列按 entity_id 稳定排列，不能视为唯一真值顺序"}
            else:
                summary["ranking"] = {"complete_roster": False, "spearman_rho": None,
                                      "reason": "参考 roster 含未纳入或没有数值的实体，不报告部分排名分数"}
        return summary


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        result, start = [0.0] * len(values), 0
        while start < len(order):
            end = start + 1
            while end < len(order) and values[order[end]] == values[order[start]]:
                end += 1
            rank = (start + 1 + end) / 2
            for index in order[start:end]:
                result[index] = rank
            start = end
        return result
    a, b = ranks(xs), ranks(ys)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    var = sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)
    return cov / math.sqrt(var) if var else 0.0


def write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=pathlib.Path, default=DEFAULT_ROOT, help="本地参考集根目录")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="审计参考记录、来源、冻结输入与哈希")
    audit.add_argument("--expected-records", type=int, default=78)
    audit.add_argument("--expected-tasks", type=int, default=11)
    audit.add_argument("--output", type=pathlib.Path, help="保存审计报告 JSON")
    fixture = sub.add_parser("fixture", help="生成仅供本地研究的结构测试答案")
    select = fixture.add_mutually_exclusive_group(required=True)
    select.add_argument("--task-id")
    select.add_argument("--task", type=pathlib.Path, help="必须与冻结 task canonical SHA-256 精确一致")
    fixture.add_argument("--output", type=pathlib.Path, required=True)
    fixture.add_argument("--allow-provisional", action="store_true")
    fixture.add_argument("--half-width", type=float, default=1.0, help="synthetic 测试区间的固定半宽")
    for name in ("validate", "compare"):
        cmd = sub.add_parser(name)
        inputs = cmd.add_mutually_exclusive_group(required=True)
        inputs.add_argument("--answer", type=pathlib.Path)
        inputs.add_argument("--answers-dir", type=pathlib.Path, help="递归读取命名为 answer.json 的文件")
        cmd.add_argument("--task", type=pathlib.Path, help="可选的外部 task，必须精确匹配冻结哈希")
        cmd.add_argument("--output", type=pathlib.Path)
        cmd.add_argument("--allow-partial", action="store_true",
                         help="仅对 --answers-dir：显式允许部分题目；默认缺题时退出2并保存完整覆盖报告")
        if name == "compare":
            cmd.add_argument("--allow-provisional", action="store_true")
    args = parser.parse_args(argv)
    try:
        exit_code = 0
        suite = ReferenceSuite(args.data_root)
        if args.command == "audit":
            result = suite.audit(args.expected_records, args.expected_tasks)
            if args.output:
                write_json(args.output, result)
        elif args.command == "fixture":
            supplied = read_json(args.task) if args.task else None
            if supplied is not None and not isinstance(supplied, dict):
                raise SuiteError("给定 task 必须为 JSON 对象")
            tid = supplied.get("task_id") if supplied is not None else args.task_id
            result = suite.fixture(tid, supplied_task=supplied, allow_provisional=args.allow_provisional,
                                   half_width=args.half_width)
            write_json(args.output, result)
            result = {"ok": True, "task_id": tid, "output": str(args.output),
                      "entity_count": len(result["entity_predictions"]), "notice": NOTICE}
        else:
            supplied = read_json(args.task) if args.task else None
            if supplied is not None and not isinstance(supplied, dict):
                raise SuiteError("给定 task 必须为 JSON 对象")
            paths = [args.answer] if args.answer else sorted(args.answers_dir.rglob("answer.json"))
            if not paths:
                raise SuiteError("没有找到 answer.json")
            reports, seen = [], set()
            for path in paths:
                answer = read_json(path)
                tid = answer.get("task_id") if isinstance(answer, dict) else None
                if tid in seen:
                    raise SuiteError(f"批量答案重复 task_id：{tid}")
                seen.add(tid)
                if args.command == "compare":
                    reports.append(suite.compare(answer, supplied_task=supplied,
                                                 allow_provisional=args.allow_provisional))
                else:
                    reports.append(suite.validate(answer, supplied))
            if args.answer:
                result = reports[0]
            else:
                missing = sorted(set(suite.units) - seen)
                complete = not missing
                result = {"ok": complete or args.allow_partial, "complete": complete,
                          "allow_partial": args.allow_partial, "tasks": reports, "task_count": len(reports),
                          "expected_task_count": len(suite.units), "missing_tasks": missing, "notice": NOTICE}
                if not complete and not args.allow_partial:
                    result["error"] = "批量答案未覆盖完整 suite；部分实验需显式 --allow-partial"
                    exit_code = 2
            if args.output:
                write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return exit_code
    except (SuiteError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "notice": NOTICE}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
