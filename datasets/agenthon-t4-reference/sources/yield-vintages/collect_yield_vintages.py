#!/usr/bin/env python3
"""公开 ALFRED 日收益率 vintage 补证；原始字节与派生摘要分开保存。

只写本脚本所在 sources/yield-vintages 目录，不改共享参考集。
download: 查询指定 observation 前一日、当日、次日三个历史 vintage。
audit: 离线重读 CSV，验证目标日期存在/缺失，与原 Treasury XML/task/reference 对照。
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1]
TASK_IDS = ["t4-fomc-curve-20220728", "t4-fomc-curve-20240918"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def tasks():
    return [json.loads((DATA / "inputs/units" / task_id / "task.json").read_text()) for task_id in TASK_IDS]


def specifications():
    items = []
    for task in tasks():
        for entity in task["entities"]:
            for role, observed in [("start", entity["as_of"]), ("end", task["resolution_date"])]:
                observed_date = date.fromisoformat(observed)
                for offset in (-1, 0, 1):
                    vintage = (observed_date + timedelta(days=offset)).isoformat()
                    beginning = (observed_date - timedelta(days=7)).isoformat()
                    series = entity["series_fred"]
                    name = f"{series}_window-{beginning}_{observed}_vintage-{vintage}.csv"
                    url = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urllib.parse.urlencode({
                        "id": series, "cosd": beginning, "coed": observed, "vintage_date": vintage})
                    items.append({"path": name, "url": url, "series_id": series, "task_id": task["task_id"],
                        "entity_id": entity["entity_id"], "role": role, "observation_date": observed,
                        "requested_vintage_date": vintage, "requested_observation_start": beginning,
                        "requested_observation_end": observed, "offset_days": offset})
    return items


def download_one(spec):
    path = HERE / spec["path"]
    metadata_path = HERE / (spec["path"] + ".metadata.json")
    if path.exists() and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("sha256") != digest(path.read_bytes()) or metadata.get("url") != spec["url"]:
            raise ValueError(f"既有证据字节/URL不一致，拒绝覆盖：{path.name}")
        return metadata
    metadata = dict(spec, retrieved_at=datetime.now(timezone.utc).isoformat(),
                    byte_form="HTTP 原始响应字节；非派生计算摘要")
    try:
        request = urllib.request.Request(spec["url"], headers={"User-Agent": "Mozilla/5.0 (public historical vintage verification)"})
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            metadata.update(http_status=response.status, content_type=response.headers.get("Content-Type"),
                            final_url=response.geturl(), sha256=digest(body), bytes=len(body), status="downloaded")
        text = body.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        column = f"{spec['series_id']}_{spec['requested_vintage_date'].replace('-', '')}"
        if reader.fieldnames != ["observation_date", column]:
            raise ValueError(f"响应不是正确 vintage CSV：{reader.fieldnames}")
        rows = list(reader)
        targets = [r for r in rows if r["observation_date"] == spec["observation_date"]]
        metadata.update(column=column, observation_rows=len(rows),
            returned_start=rows[0]["observation_date"] if rows else None,
            returned_end=rows[-1]["observation_date"] if rows else None,
            target_observation_present=len(targets) == 1,
            target_raw_value=targets[0][column] if len(targets) == 1 else None)
        path.write_bytes(body)
    except Exception as error:
        metadata.update(status="download_failed", error=f"{type(error).__name__}: {error}")
    save(metadata_path, metadata)
    return metadata


def download():
    specifications_list = specifications()
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_one, spec): spec for spec in specifications_list}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(result["series_id"], result["observation_date"], result["requested_vintage_date"],
                  result["status"], "target=", result.get("target_raw_value"), flush=True)
    save(HERE / "downloads.json", sorted(results, key=lambda x: (x["task_id"], x["entity_id"], x["role"], x["requested_vintage_date"])))
    return results


def xml_rates(year):
    p = DATA / "sources/treasury" / f"yield_curve_{year}.xml"
    d = "{http://schemas.microsoft.com/ado/2007/08/dataservices}"
    m = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"
    rows = [{x.tag.removeprefix(d): x.text for x in n} for n in ET.parse(p).getroot().iter(m + "properties")]
    return p, rows


def audit():
    specs = specifications()
    rereads = []
    for spec in specs:
        metadata = json.loads((HERE / (spec["path"] + ".metadata.json")).read_text())
        if metadata["status"] != "downloaded":
            rereads.append(dict(metadata, independent_check="download_failed")); continue
        raw = (HERE / spec["path"]).read_bytes()
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        column = f"{spec['series_id']}_{spec['requested_vintage_date'].replace('-', '')}"
        rows = list(reader)
        selected = [r for r in rows if r["observation_date"] == spec["observation_date"]]
        entry = dict(metadata, hash_matches=digest(raw) == metadata["sha256"],
                     vintage_column_matches=reader.fieldnames == ["observation_date", column],
                     independent_target_present=len(selected) == 1,
                     independent_value=float(selected[0][column]) if len(selected) == 1 and selected[0][column] not in ("", ".") else None)
        rereads.append(entry)
    references = [json.loads(line) for line in (DATA / "reference.jsonl").read_text().splitlines() if line.strip()]
    ref_by_key = {(r["task_id"], r["entity_id"]): r for r in references}
    records = []
    for task in tasks():
        xml_path, rows = xml_rates(task["cutoff_date"][:4])
        for entity in task["entities"]:
            key = (task["task_id"], entity["entity_id"])
            record = {"task_id": key[0], "entity_id": key[1], "series_id": entity["series_fred"],
                "unit": "bps_change", "start_observation_date": entity["as_of"], "end_observation_date": task["resolution_date"],
                "task_start_yield_pct": entity["start_yield_pct"], "existing_reference_value_bps": ref_by_key[key]["reference_value"],
                "endpoint_evidence": {}, "checks": {}, "findings": []}
            values = {}
            for role in ("start", "end"):
                candidates = sorted([r for r in rereads if r["task_id"] == key[0] and r["entity_id"] == key[1] and r["role"] == role],
                                    key=lambda r: r["requested_vintage_date"])
                available = [r for r in candidates if r.get("independent_value") is not None]
                earliest = available[0] if available else None
                previous = [r for r in candidates if earliest and r["requested_vintage_date"] < earliest["requested_vintage_date"]]
                observed = entity["as_of"] if role == "start" else task["resolution_date"]
                field = f"BC_{entity['maturity_years']}YEAR"
                selected_xml = [r for r in rows if r["NEW_DATE"][:10] == observed]
                if len(selected_xml) != 1:
                    raise ValueError("Treasury XML observation 唯一码不成立")
                xml_value = float(selected_xml[0][field])
                values[role] = earliest["independent_value"] if earliest else None
                evidence = {"observation_date": observed, "probes": [{k: r.get(k) for k in
                    ("path", "url", "requested_vintage_date", "status", "hash_matches", "vintage_column_matches", "independent_target_present", "independent_value", "returned_start", "returned_end")} for r in candidates],
                    "earliest_tested_available_vintage": earliest["requested_vintage_date"] if earliest else None,
                    "earliest_tested_available_value_pct": values[role], "current_Treasury_XML_value_pct": xml_value,
                    "prior_tested_vintages_target_absent": bool(previous) and all(r.get("status") == "downloaded" and r.get("independent_target_present") is False for r in previous),
                    "global_source_first_publication_proven": False,
                    "source_first_publication_date": None,
                    "ALFRED_release_date_basis": "CSV 的 as-of vintage 日期；未取得本次具体行的原始源发布时间或 realtime_start API 字段"}
                record["endpoint_evidence"][role] = evidence
                record["checks"][f"{role}_historical_csv_available"] = earliest is not None
                record["checks"][f"{role}_all_downloaded_hashes_and_columns_match"] = all(r.get("hash_matches") is True and r.get("vintage_column_matches") is True for r in candidates)
                record["checks"][f"{role}_previous_vintages_target_absent"] = evidence["prior_tested_vintages_target_absent"]
                record["checks"][f"{role}_historical_value_equals_current_XML"] = values[role] == xml_value
                record["checks"][f"{role}_latest_observation_not_future_of_vintage"] = all(r.get("returned_end", "9999") <= r["requested_vintage_date"] for r in candidates if r.get("status") == "downloaded")
            if None not in values.values():
                bps = float((Decimal(str(values["end"])) - Decimal(str(entity["start_yield_pct"]))) * 100)
                record.update(historical_start_pct=values["start"], historical_end_pct=values["end"],
                    recomputed_bps=bps, difference_vs_existing_reference_bps=bps - record["existing_reference_value_bps"],
                    formula="100 * (earliest_tested_end_vintage_yield_pct - task.start_yield_pct)")
                record["checks"]["historical_start_equals_frozen_task"] = values["start"] == entity["start_yield_pct"]
                record["checks"]["historical_bps_equals_existing_reference"] = bps == record["existing_reference_value_bps"]
            record["pass_flag"] = all(record["checks"].values())
            record["status"] = "historical_vintage_verified" if record["pass_flag"] else "needs_review"
            record["findings"].append("最早可见日仅指所查询前一日/当日/次日 ALFRED vintage 的转变；不是全球首发或 Treasury 同日网页首发证明。")
            record["findings"].append("起点任务值为 observation day close 的冻结已给定数字；ALFRED 收录日在次日不撤销题面已给定 baseline。")
            records.append(record)
    summary = {"task_count": 2, "entity_count": len(records), "endpoint_count": 24,
        "requested_csvs": len(specs), "downloaded_csvs": sum(r["status"] == "downloaded" for r in rereads),
        "endpoint_historical_vintage_available": sum(e["earliest_tested_available_vintage"] is not None for r in records for e in r["endpoint_evidence"].values()),
        "reference_value_differences": sum(r.get("difference_vs_existing_reference_bps", 1) != 0 for r in records),
        "entities_passed": sum(r["pass_flag"] for r in records),
        "all_entity_checks_pass": all(r["pass_flag"] for r in records),
        "global_source_first_publication_proven": False}
    report = {"schema_version": "0.1.0", "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": {"python_version": sys.version, "platform": platform.platform(),
            "script_sha256": digest(Path(__file__).read_bytes()), "command": "python3 datasets/agenthon-t4-reference/sources/yield-vintages/collect_yield_vintages.py audit"},
        "reference_snapshot": {"path": "reference.jsonl", "sha256": digest((DATA / "reference.jsonl").read_bytes())},
        "summary": summary, "records": records,
        "existing_input_hashes": [{"path": str(DATA / "inputs/units" / t / "task.json"),
            "sha256": digest((DATA / "inputs/units" / t / "task.json").read_bytes())} for t in TASK_IDS] +
            [{"path": str(DATA / "sources/treasury" / f"yield_curve_{year}.xml"),
                "sha256": digest((DATA / "sources/treasury" / f"yield_curve_{year}.xml").read_bytes())} for year in (2022, 2024)]}
    save(HERE / "vintage-comparison.json", report)
    manifest_sources = []
    for p in sorted(HERE.glob("*.metadata.json")):
        m = json.loads(p.read_text())
        manifest_sources.append({"path": m.get("path"), "url": m.get("url"), "sha256": m.get("sha256"),
            "bytes": m.get("bytes"), "retrieved_at": m.get("retrieved_at"), "status": m.get("status", "downloaded"),
            "locator": m.get("locator") or f"observation_date={m.get('observation_date')}; vintage={m.get('requested_vintage_date')}; column={m.get('column') or str(m.get('series_id'))+'_'+str(m.get('requested_vintage_date')).replace('-', '')}",
            "published_at": m.get("published_at"), "vintage_date": m.get("requested_vintage_date"),
            "published_at_basis": "源首发日期未独立证明；vintage_date 与 retrieved_at 分开", "error": m.get("error")})
    for name, locator in [
            ("vintage-comparison.json", "records；由保存原始 CSV/XML/task 复算，不是源原始响应"),
            ("primary-context-evidence.json", "官方说明的既有web浏览摘录；不是HTTP原始响应，哈希只识别本地摘录文件"),
            ("yield-vintage-report.md", "12实体中文研究报告；不是源原始响应")]:
        p = HERE / name
        if p.exists():
            report_raw = p.read_bytes()
            manifest_sources.append({"path": name, "url": None,
                "sha256": digest(report_raw), "bytes": len(report_raw), "retrieved_at": report["checked_at"],
                "status": "derived_summary", "locator": locator, "published_at": None})
    save(HERE / "evidence-manifest.json", {"schema_version": "0.1.0", "sources": manifest_sources,
        "checks": [{"task_id": r["task_id"], "entity_id": r["entity_id"], "checks": r["checks"], "pass_flag": r["pass_flag"]} for r in records],
        "limitations": [
            "ALFRED vintage CSV 支持按历史 as-of 日期重建当时可见数字；release date 的依据可能是源、provider 或 FRED首次可用日期，不能无证据等同 Treasury全球首发日。",
            "本次逐 endpoint 查询 observation 前一日/当日/次日；最早可见 vintage 是在连续日边界的实际查询结果，而非精确盘中时间戳证明。",
            "未取得四个目标日期 Treasury 同日网页的独立存档或 H.15 原始历史日稿；当前 XML 与早期ALFRED数字完全一致也不能填补全球首发链。",
            "单日future-range ALFRED 请求可能回退返回整段历史；所有返回均保留原字节并实际按 observation_date筛选，不能只凭文件名或参数认定目标日在该 vintage存在。"]})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["download", "audit"])
    args = parser.parse_args()
    if args.action == "download":
        download()
    else:
        audit()
