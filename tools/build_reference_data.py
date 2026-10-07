#!/usr/bin/env python3
"""冻结公开输入、复算 COT、合并研究记录；仅用于本地参考集。"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets/agenthon-t4-reference"
COMMIT = "1c744e1d6725340643a533f436517d72b53ca0e1"
REFERENCE_VERSION = "0.2.1"
REPO = "https://github.com/Agenthon-2026/track4-analysis-public"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args])


def freeze(source, toolkit_source):
    """直接读取固定 commit 的 blob，避免把工作区改动当官方版本。"""
    dest = DATA / "inputs"
    paths = git(source, "ls-tree", "-r", "--name-only", COMMIT, "--", "units").decode().splitlines()
    if any("outcome" in p.lower() or "/reference/" in p for p in paths):
        raise ValueError("公开输入发现不应复制的 outcome/reference 路径")
    rows, tasks = [], []
    for p in paths + ["LICENSE", "DATA-LICENSE.md", "THIRD-PARTY-NOTICES.md"]:
        payload = git(source, "show", f"{COMMIT}:{p}")
        target = dest / p
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != payload:
            raise ValueError(f"冻结路径已有不同内容，拒绝覆盖：{target}")
        target.write_bytes(payload)
        rows.append({"path": p, "sha256": sha(payload), "bytes": len(payload)})
        if p.endswith("/task.json"):
            t = json.loads(payload)
            tasks.append({"task_id": t["task_id"], "task_path": p,
                          "task_sha256": sha(payload), "task_canonical_sha256": sha(canonical(t)),
                          "target_type": t["target"]["type"], "target_name": t["target"]["name"],
                          "cutoff_date": t["cutoff_date"], "resolution_date": t["resolution_date"],
                          "entity_ids": [e["entity_id"] for e in t["entities"]]})
    tasks.sort(key=lambda t: t["task_id"])
    assert len(tasks) == 11 and sum(len(t["entity_ids"]) for t in tasks) == 78
    assert len({t["task_id"] for t in tasks}) == 11
    for t in tasks:
        prefix = str(Path(t["task_path"]).parent) + "/"
        t["files"] = [r for r in rows if r["path"].startswith(prefix)]
    schemas = []
    toolkit_commit = "50fb2dc2b39c70f4cf81fcd269943782eddfaed0"
    for original, local in [("common/qfbench2_common/schemas/analysis.schema.json", "schemas/analysis.schema.json"),
                            ("common/LICENSE", "schemas/LICENSE")]:
        payload = git(toolkit_source, "show", f"{toolkit_commit}:{original}")
        target = dest / local
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != payload:
            raise ValueError(f"冻结 schema 已有不同字节：{target}")
        target.write_bytes(payload)
        schemas.append({"path": local, "sha256": sha(payload), "source_commit": toolkit_commit,
                        "source_repository": "https://github.com/Agenthon-2026/Agenthon2026-public", "source_path": original})
    save(dest / "source-manifest.json", {
        "schema_version": "0.1.0", "source_repository": REPO, "source_commit": COMMIT,
        "copied_at": datetime.now(timezone.utc).isoformat(),
        "task_count": 11, "entity_count": 78, "units": tasks,
        "license_files": [r for r in rows if not r["path"].startswith("units/")], "schemas": schemas})
    print(json.dumps({"frozen_tasks": 11, "entities": 78, "files": len(rows)}, ensure_ascii=False))


def cot():
    p = DATA / "sources/cot"
    a = json.loads((p / "legacy-futures-only-20241022-20241126.json").read_text())
    with zipfile.ZipFile(p / "deacot2024.zip") as z:
        archived = list(csv.DictReader(io.StringIO(z.read("annual.txt").decode("utf-8-sig"))))
    task = json.loads((DATA / "inputs/units/t4-cotpos-202411-us10/task.json").read_text())
    records, checks = [], []
    url = (p / "query-url.txt").read_text().strip()
    for e in task["entities"]:
        matches = [r for r in a if r["report_date_as_yyyy_mm_dd"].startswith("2024-10-22")
                   and int(r["open_interest_all"]) == e["open_interest_20241022"]
                   and int(r["noncomm_positions_long_all"]) - int(r["noncomm_positions_short_all"]) == e["net_noncommercial_20241022"]]
        assert len(matches) == 1, (e["entity_id"], len(matches))
        start = matches[0]
        code = start["cftc_contract_market_code"]
        ends = [r for r in a if r["report_date_as_yyyy_mm_dd"].startswith("2024-11-26") and r["cftc_contract_market_code"] == code]
        assert len(ends) == 1, code
        end = ends[0]
        for r in [start, end]:
            date = r["report_date_as_yyyy_mm_dd"][:10]
            ar = [x for x in archived if x["As of Date in Form YYYY-MM-DD"].strip() == date
                  and x["CFTC Contract Market Code"].strip() == code]
            assert len(ar) == 1, (code, date)
            for api, annual in [("open_interest_all", "Open Interest (All)"),
                                ("noncomm_positions_long_all", "Noncommercial Positions-Long (All)"),
                                ("noncomm_positions_short_all", "Noncommercial Positions-Short (All)")]:
                assert int(r[api]) == int(ar[0][annual]), (code, date, api)
        snet = int(start["noncomm_positions_long_all"]) - int(start["noncomm_positions_short_all"])
        enet = int(end["noncomm_positions_long_all"]) - int(end["noncomm_positions_short_all"])
        val = 100 * (enet - snet) / int(start["open_interest_all"])
        records.append({"task_id": task["task_id"], "entity_id": e["entity_id"], "target_type": "ranking",
                        "reference_label": None, "reference_value": val, "unit": "pct_of_open_interest",
                        "status": "verified", "method": "100 × (11月26日非商业多头减空头 − 10月22日非商业多头减空头) / 10月22日open interest；按值降序排序。",
                        "inputs": [{"name": "start_net", "value": snet, "date": "2024-10-22", "unit": "contracts"},
                                   {"name": "end_net", "value": enet, "date": "2024-11-26", "unit": "contracts"},
                                   {"name": "start_open_interest", "value": int(start["open_interest_all"]), "date": "2024-10-22", "unit": "contracts"}],
                        "sources": [{"url": url, "title": "CFTC Legacy Futures Only 两期报告 API", "published_at": None,
                                     "locator": f"CFTC contract market code={code}; report_date=2024-10-22/2024-11-26; noncomm_positions_long_all/short_all/open_interest_all"},
                                    {"url": "https://www.cftc.gov/files/dea/history/deacot2024.zip", "title": "CFTC 2024 Legacy Futures Only 年度历史压缩数据", "published_at": None,
                                     "locator": f"annual.txt; CFTC Contract Market Code={code}; As of Date=2024-10-22/2024-11-26"}],
                        "notes": [f"市场代码{code}，名称{start['market_and_exchange_names']}；Legacy futures only，不含options、不采用TFF或disaggregated分类。",
                                  "20个市场日期行的open interest、noncommercial long、short在官方API与年度历史文件一致；10个task基期net/OI均一致。",
                                  "使用报告as-of日期，非下载日；年度文件与当前API未提供本次行的历史修订链，因此尚未证明这两份数据均等于当时首次发布版本。",
                                  "verified表示公开资料复核完成，不表示与主办方私有outcome比对一致。"]})
        checks.append({"entity_id": e["entity_id"], "contract_code": code, "baseline_matches_task": True, "annual_api_equal": True, "reference_value": val})
    for rank, r in enumerate(sorted(records, key=lambda x: x["reference_value"], reverse=True), 1):
        r["reference_rank"] = rank
    save(DATA / "research/cot.json", {"schema_version": "0.1.0", "group": "cot", "records": records})
    save(p / "verification.json", {"checks": checks, "rows": 10, "api_annual_comparisons": 20,
                                   "first_published_vintage_verified": False})
    metadata = []
    for f, u in [(p / "deacot2024.zip", "https://www.cftc.gov/files/dea/history/deacot2024.zip"),
                 (p / "legacy-futures-only-20241022-20241126.json", url)]:
        metadata.append({"path": f.name, "url": u, "sha256": sha(f.read_bytes()), "retrieved_at": datetime.now(timezone.utc).isoformat(),
                         "byte_form": "API JSON本地格式化副本" if f.suffix == ".json" else "下载原始压缩字节"})
    save(p / "downloads.json", metadata)
    lines = ["# COT 持仓变化参考结果", "", "10 个实体已用 CFTC 官方 API 与年度 Legacy Futures Only 历史文件逐行核对。首次发布版本的修订链仍未证明，不能据此宣称满足正式 fitting provenance 的首次发布值条件。", "", "| entity_id | 市场代码 | 起始净持仓 | 结束净持仓 | 变化 / 起始 OI（%） | 排名 |", "| --- | --- | ---: | ---: | ---: | ---: |"]
    for r, c in zip(records, checks):
        lines.append(f"| {r['entity_id']} | {c['contract_code']} | {r['inputs'][0]['value']} | {r['inputs'][1]['value']} | {r['reference_value']:.10f} | {r['reference_rank']} |")
    lines += ["", "计算式：`100 * (end_net - start_net) / start_open_interest`。排名 1 表示向净多头移动幅度最大。分母固定使用 2024-10-22 的 open interest，不能改为结束期或净持仓百分比之差。", "", "[官方 Legacy Futures Only 数据集](https://publicreporting.cftc.gov/Commitments-of-Traders/Legacy-Futures-Only/6dca-aqww)；[年度原始 ZIP](https://www.cftc.gov/files/dea/history/deacot2024.zip)。准确查询 URL 与原始资料 hash 见 sources/cot/downloads.json；复算记录见 sources/cot/verification.json。", ""]
    (DATA / "research/cot.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False))


def combine():
    manifest = json.loads((DATA / "inputs/source-manifest.json").read_text())
    expected = [(u["task_id"], e) for u in manifest["units"] for e in u["entity_ids"]]
    rows = []
    for group in ["treasury", "macro", "earnings-credit", "cot"]:
        rows.extend(json.loads((DATA / "research" / f"{group}.json").read_text())["records"])
    by_key = {(r["task_id"], r["entity_id"]): r for r in rows}
    if len(by_key) != len(rows) or set(by_key) != set(expected):
        raise ValueError(f"参考记录覆盖错误 missing={set(expected)-set(by_key)} extra={set(by_key)-set(expected)}")
    units = {u["task_id"]: u for u in manifest["units"]}
    resolution = DATA / "research/resolution-overrides.json"
    overrides = {}
    if resolution.is_file():
        for record in json.loads(resolution.read_text())["records"]:
            key = (record["task_id"], record["entity_id"])
            if key in overrides or key not in by_key:
                raise ValueError(f"收敛记录重复或不属于roster：{key}")
            overrides[key] = record
    ordered = []
    for key in expected:
        r = dict(by_key[key])
        r["quality"] = {"fact_status": "verified" if r["status"] == "verified" else r["status"],
                        "task_alignment": "aligned", "first_publication_status": "unconfirmed",
                        "official_outcome_status": "unconfirmed",
                        "acceptance_scope": "按已登记公开来源和题面定义进行本地历史结果核对；首次全球发布版本与官方私有outcome未确认。"}
        if key in overrides:
            r.update({k: v for k, v in overrides[key].items() if k not in {"task_id", "entity_id"}})
        r["task_canonical_sha256"] = units[key[0]]["task_canonical_sha256"]
        ordered.append(r)
    (DATA / "reference.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in ordered), encoding="utf-8")
    with (DATA / "reference.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["task_id", "entity_id", "target_type", "reference_label", "reference_value", "reference_rank", "unit", "status",
                  "fact_status", "task_alignment", "first_publication_status", "official_outcome_status"]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(dict(r, **{k: r["quality"][k] for k in fields[-4:]}) for r in ordered)
    counts = {s: sum(r["status"] == s for r in ordered) for s in ["verified", "provisional", "unresolved"]}
    save(DATA / "build-report.json", {"schema_version": "0.2.0", "reference_version": REFERENCE_VERSION, "source_commit": COMMIT,
                                    "tasks": 11, "entities": 78, "statuses": counts,
                                    "quality_counts": {k: {v: sum(r["quality"][k] == v for r in ordered)
                                                        for v in sorted({r["quality"][k] for r in ordered})}
                                                       for k in ["fact_status", "task_alignment", "first_publication_status", "official_outcome_status"]},
                                    "reference_sha256": sha((DATA / "reference.jsonl").read_bytes()),
                                    "official_evaluation": None, "official_score": None})
    print(counts)


def manifest():
    """登记交付快照的精确字节；不把此登记冒充独立来源证明。"""
    entries = [{"path": p.relative_to(DATA).as_posix(), "sha256": sha(p.read_bytes()),
                "bytes": p.stat().st_size}
               for p in sorted(DATA.rglob("*")) if p.is_file() and not p.is_symlink()
               and not {".local", "_private", "__pycache__"}.intersection(p.relative_to(DATA).parts)
               and p.name != "dataset-manifest.json"]
    build = json.loads((DATA / "build-report.json").read_text())
    save(DATA / "dataset-manifest.json", {
        "schema_version": "0.1.0", "reference_version": build.get("reference_version", REFERENCE_VERSION),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_count": build["tasks"], "entity_count": build["entities"],
        "status_counts": build["statuses"], "reference_sha256": sha((DATA / "reference.jsonl").read_bytes()),
        "file_count": len(entries), "files": entries,
        "official_evaluation": None, "official_score": None,
        "notice": "本地交付文件精确快照索引；不替代独立原件/首次发布版本的证据审校。"})
    print(json.dumps({"files": len(entries), "bytes": sum(r["bytes"] for r in entries)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "cot", "combine", "manifest"])
    parser.add_argument("--source", type=Path)
    parser.add_argument("--toolkit-source", type=Path)
    args = parser.parse_args()
    if args.action == "freeze":
        if not args.source or not args.toolkit_source:
            parser.error("freeze 需要 --source 和 --toolkit-source 指定两个官方 Git 检出")
        freeze(args.source, args.toolkit_source)
    elif args.action == "cot":
        cot()
    elif args.action == "combine":
        combine()
    else:
        manifest()
