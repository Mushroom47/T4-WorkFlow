#!/usr/bin/env python3
"""使用固定官方源码检查本地实验输出的 schema、alignment 与确定性引用。"""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets/agenthon-t4-reference"
COMMIT = "1c744e1d6725340643a533f436517d72b53ca0e1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--answers-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 13):
        raise RuntimeError("官方工具要求 Python >= 3.13")
    head = subprocess.check_output(["git", "-C", str(args.official_root), "rev-parse", "HEAD"], text=True).strip()
    if head != COMMIT:
        raise RuntimeError(f"官方源码 commit 不匹配：{head}")
    sys.path.insert(0, str(args.official_root.resolve()))
    import jsonschema
    from importlib.resources import files
    from qfbench2_track_analysis.alignment import EntityRoster, align_predictions
    from qfbench2_track_analysis.scoring import SCORER_VERSION
    from baselines.guardrails_example.citation_rail import (
        check_claim_rules, check_submitted_reasons, load_corpus,
    )
    if importlib.metadata.version("qfbench2-common") != "2.5.1" or SCORER_VERSION != "5.2.2":
        raise RuntimeError("package/scorer 版本不匹配")
    schema_bytes = (files("qfbench2_common") / "schemas/analysis.schema.json").read_bytes()
    if schema_bytes != (DATA / "inputs/schemas/analysis.schema.json").read_bytes():
        raise RuntimeError("安装的 schema 与冻结原件不同")
    validator = jsonschema.Draft202012Validator(json.loads(schema_bytes))
    manifests = json.loads((DATA / "inputs/source-manifest.json").read_text())
    units = {u["task_id"]: DATA / "inputs" / Path(u["task_path"]).parent for u in manifests["units"]}
    reports, seen = [], set()
    for path in sorted(args.answers_dir.rglob("answer.json")):
        answer = json.loads(path.read_text())
        tid = answer["task_id"]
        if tid in seen:
            raise RuntimeError(f"重复task：{tid}")
        seen.add(tid)
        unit = units[tid]
        task = json.loads((unit / "task.json").read_text())
        validator.validate(answer)
        align_predictions(answer, EntityRoster.from_task(task), target_type=task["target"]["type"], interval_level=0.90)
        findings = check_claim_rules(answer, unit, token_counter=None)
        reasons = check_submitted_reasons(answer, load_corpus(unit / "corpus"), task["cutoff_date"])
        hard = [f for f in findings if f.code != "claim_tokens_unchecked"]
        reports.append({"task_id": tid, "entity_count": len(task["entities"]), "schema_pass": True,
                        "alignment_pass": True, "claim_findings": [asdict(f) for f in findings],
                        "reason_findings": [asdict(f) for f in reasons],
                        "deterministic_pass": not hard and not reasons})
    report = {"ok": seen == set(units) and all(r["deterministic_pass"] for r in reports),
              "source_commit": COMMIT, "scorer_version": SCORER_VERSION, "python": sys.version,
              "packages": {n: importlib.metadata.version(n) for n in ["qfbench2-common", "jsonschema", "numpy", "scipy"]},
              "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(), "tasks": reports,
              "task_count": len(reports), "entity_count": sum(r["entity_count"] for r in reports),
              "missing_tasks": sorted(set(units) - seen),
              "claim_findings_counts": dict(Counter(f["code"] for r in reports for f in r["claim_findings"])),
              "official_evaluation": False, "official_score": None,
              "not_executed": ["production NLI contradiction", "judge 400-token cap", "Final reasoning grader", "private outcome/naive scoring", "官方平台评测"],
              "notice": "只执行公开官方代码的本地确定性检查；fixture自测不证明预测能力。"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "tasks"}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
