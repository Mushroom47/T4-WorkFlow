#!/usr/bin/env python3
"""只读核对 postearn 的有限窗口和公式；不会联网、更新共享参考或写外部文件。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DATES = ["2024-02-01", "2024-02-02"]
SYMBOLS = ("AAPL", "AMZN", "META", "SPY")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cents(value) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def label(value: Fraction) -> str:
    return "positive_reaction" if value > 1 else "negative_reaction" if value < -1 else "flat"


def xlsx_spy_rows(path: Path) -> list[dict]:
    """直接解析工作簿，避免把已有派生提取结果作为原件自比。"""
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            tree = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in si.findall(".//s:t", NS)) for si in tree.findall("s:si", NS)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = next(s for s in workbook.findall("s:sheets/s:sheet", NS) if s.attrib["name"] == "dividend")
        relation = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(r.attrib["Target"] for r in relations if r.attrib["Id"] == relation)
        sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        root = ET.fromstring(archive.read(sheet_path))
        rows = []
        for row in root.findall("s:sheetData/s:row", NS):
            fields = {}
            for cell in row.findall("s:c", NS):
                coordinate = cell.attrib["r"]
                column = "".join(c for c in coordinate if c.isalpha())
                v = cell.find("s:v", NS)
                value = "" if v is None else v.text or ""
                if cell.attrib.get("t") == "s":
                    value = strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                fields[column] = value.strip()
            if fields.get("B") == "SPY":
                rows.append({"row": int(row.attrib["r"]), "fields": fields})
        return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="可选：本地完整 dataset 目录，回读上游证据；未提供时仅复算公开派生事实")
    parser.add_argument("--reference", type=Path, help="可选：只读比较共享 reference.jsonl，不更新状态")
    parser.add_argument("--report", type=Path, help="可选：保存 JSON 报告；输出限于脚本所在目录")
    parser.add_argument("--full-report", action="store_true", help="将本次实际检查数组输出到标准输出，供主审计工具调用")
    args = parser.parse_args()
    data = load(HERE / "normalized-evidence.json")
    checks = []

    def check(name, actual, expected):
        checks.append({"check": name, "pass": actual == expected, "actual": actual, "expected": expected})

    check("官方题卡指定 Yahoo 日收盘", data["contract"]["price_source"], "Yahoo Finance (daily closes for outcome resolution)")
    check("目标日期", data["contract"]["dates"], DATES)
    check("公司收益口径", data["contract"]["company_return_type"], "total_return")
    for symbol in SYMBOLS:
        row = data["prices"][symbol]
        check(symbol + " 标的", row["meta"]["symbol"], symbol)
        check(symbol + " 币种", row["meta"]["currency"], "USD")
        check(symbol + " 历史日期", row["dates"], DATES)
        check(symbol + " 证券类型", row["meta"]["instrumentType"], "ETF" if symbol == "SPY" else "EQUITY")
        check(symbol + " priceHint", row["meta"]["priceHint"], 2)
        check(symbol + " 美分规范化", [cents(p) for p in row["close_float"]], row["close_cents"])
        check(symbol + " 有限正价格", all(math.isfinite(float(p)) and float(p) > 0 for p in row["close_float"] + row["adjclose_float"]), True)
        check(symbol + " Yahoo 事件列表", row["events"], {})
        check(symbol + " Q4 美分旁证", row["q4_close_cents"], row["close_cents"])
        check(symbol + " 两日分配调整因子无实质阶跃", abs((row["adjclose_float"][1] / row["close_float"][1]) / (row["adjclose_float"][0] / row["close_float"][0]) - 1) < 2e-7, True)

    action = data["corporate_actions"]
    check("AAPL 对应除息日", action["AAPL"]["ex_date"], "2024-02-09")
    check("META 首次除息日", action["META"]["ex_date"], "2024-02-21")
    check("AAPL/META 窗口现金分配", all(action[s]["ex_date"] not in DATES for s in ("AAPL", "META")), True)
    check("AMZN 发行人从未现金分红陈述", action["AMZN"]["issuer_states_never_paid_cash_dividends"], True)
    check("AMZN 发行人列示的最近拆股在窗口外", action["AMZN"]["last_split_effective_date"] < DATES[0], True)
    check("SPY 全分配表窗口匹配数", action["SPY"]["window_ex_date_match_count"], 0)

    original_checks = []
    if args.source_root:
        original_root = args.source_root.resolve()
        for source in data["local_originals"]:
            path = original_root / source["path"]
            if not path.is_file():
                check("原件存在 " + source["path"], False, True)
                continue
            body = path.read_bytes()
            check("原件 hash " + source["path"], hashlib.sha256(body).hexdigest(), source["sha256"])
            check("原件 bytes " + source["path"], len(body), source["bytes"])
            original_checks.append(source["path"])
        unit = original_root / "inputs/units/t4-postearn-20240201-megacap"
        if (unit / "card.toml").is_file():
            card = tomllib.loads((unit / "card.toml").read_text())
            check("原始题卡指定 Yahoo", "Yahoo Finance (daily closes for outcome resolution)" in card["provenance"]["data_source"], True)
            check("原始题卡 forecast cutoff", card["provenance"]["data_cutoff"], "2024-01-31")
        if (unit / "task.json").is_file():
            task = load(unit / "task.json")
            check("原始 task_id", task["task_id"], data["contract"]["task_id"])
            check("原始题面 total return 窗口", "company total return from the 2024-02-01 close to the 2024-02-02 close" in task["prompt"], True)
        for symbol in SYMBOLS:
            raw_path = original_root / f"sources/earnings-credit/yahoo-{symbol}-20240201-20240202.raw.json"
            if not raw_path.is_file():
                continue
            result = load(raw_path)["chart"]["result"][0]
            row = data["prices"][symbol]
            for key, value in row["meta"].items():
                check(symbol + " 原件元数据 " + key, result["meta"][key], value)
            dates = [datetime.fromtimestamp(t, ZoneInfo(result["meta"]["exchangeTimezoneName"])).date().isoformat() for t in result["timestamp"]]
            check(symbol + " 原件历史日期", dates, DATES)
            check(symbol + " 原件 close", result["indicators"]["quote"][0]["close"], row["close_float"])
            check(symbol + " 原件 adjclose", result["indicators"]["adjclose"][0]["adjclose"], row["adjclose_float"])
            check(symbol + " 原件事件", result.get("events", {}), {})
        for symbol, filename in (("AAPL", "apple-nasdaq-dividend.json"), ("META", "meta-nasdaq-dividend.json")):
            path = original_root / "sources/postearn-supplement" / filename
            if not path.is_file():
                continue
            rows = load(path)["data"]["dividends"]["rows"]
            relevant = [r for r in rows if datetime.strptime(r["exOrEffDate"], "%m/%d/%Y").date().isoformat() == action[symbol]["ex_date"]]
            check(symbol + " 原始除息记录命中数", len(relevant), 1)
            matches = [r for r in rows if datetime.strptime(r["exOrEffDate"], "%m/%d/%Y").date().isoformat() in DATES]
            check(symbol + " 原始分红表窗口匹配数", len(matches), 0)
        path = original_root / "sources/postearn-supplement/spy-ssga-distributions.xlsx"
        if path.is_file():
            spy_rows = xlsx_spy_rows(path)
            check("原始 SSGA SPY 行数", len(spy_rows), action["SPY"]["full_table_spy_row_count"])
            check("原始 SSGA SPY CUSIP", sorted({r["fields"].get("C") for r in spy_rows}), ["78462F103"])
            matches = [r["row"] for r in spy_rows if datetime.strptime(r["fields"]["D"], "%m/%d/%Y").date().isoformat() in DATES]
            check("原始 SSGA 分配窗口匹配", matches, [])

    returns = {}
    benchmark = data["prices"]["SPY"]["close_cents"]
    spy_return = (Fraction(benchmark[1]) / Fraction(benchmark[0]) - 1) * 100
    reference = {}
    if args.reference:
        reference = {r["entity_id"]: r for r in map(json.loads, args.reference.read_text().splitlines()) if r["task_id"] == data["contract"]["task_id"]}
    for symbol in SYMBOLS[:-1]:
        row = data["prices"][symbol]
        company_return = (Fraction(row["close_cents"][1]) / Fraction(row["close_cents"][0]) - 1) * 100
        value = company_return - spy_return
        spy_adj = data["prices"]["SPY"]["adjclose_float"]
        adj_value = ((row["adjclose_float"][1] / row["adjclose_float"][0] - 1) - (spy_adj[1] / spy_adj[0] - 1)) * 100
        raw_spy = data["prices"]["SPY"]["close_float"]
        raw_value = ((row["close_float"][1] / row["close_float"][0] - 1) - (raw_spy[1] / raw_spy[0] - 1)) * 100
        expected = data["resolution"][symbol]
        check(symbol + " 美分有理数重算", abs(float(value) - expected["reference_value"]) < 1e-10, True)
        check(symbol + " 分类阈值", label(value), expected["reference_label"])
        check(symbol + " raw float 与美分口径差异", abs(raw_value - float(value)) < 2e-5, True)
        check(symbol + " adjclose 与美分口径差异", abs(adj_value - float(value)) < 2e-5, True)
        check(symbol + " adjclose 标签", label(Fraction(str(adj_value))), label(value))
        returns[symbol] = {"company_return_percent": float(company_return), "spy_return_percent": float(spy_return), "abnormal_return_percent": float(value), "exact_fraction_percentage_points": f"{value.numerator}/{value.denominator}", "reference_label": label(value), "raw_float_abnormal_return_percent": raw_value, "adjclose_abnormal_return_percent": adj_value, "proposed_local_status": "verified", "quality": {"fact_status": "verified", "task_alignment": "aligned", "first_publication_status": "unconfirmed", "official_outcome_status": "unconfirmed"}}
        if args.reference:
            check(symbol + " 共享参考值", abs(reference[symbol]["reference_value"] - float(value)) < 1e-10, True)
            check(symbol + " 共享参考标签", reference[symbol]["reference_label"], label(value))
    failed = [c for c in checks if not c["pass"]]
    if failed:
        for row in returns.values():
            row["proposed_local_status"] = "verification_failed"
            row["quality"]["fact_status"] = "verification_failed"
    report = {"task_id": data["contract"]["task_id"], "generated_at": datetime.now(timezone.utc).isoformat(), "verification_mode": "local_originals_and_derived_values" if args.source_root else "derived_values_only", "passed": not failed, "check_count": len(checks), "failed_count": len(failed), "checks": checks, "original_files_read": original_checks, "returns": returns, "limitations": data["limitations"]}
    if args.report:
        destination = args.report.resolve()
        if not destination.is_relative_to(HERE):
            parser.error("--report 仅允许写入 postearn-resolution 目录")
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    printed = report if args.full_report else {k: report[k] for k in ("verification_mode", "passed", "check_count", "failed_count", "returns")}
    print(json.dumps(printed, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
