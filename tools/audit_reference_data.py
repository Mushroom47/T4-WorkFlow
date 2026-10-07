#!/usr/bin/env python3
"""离线独立审校公开历史参考集；只读取已保存资料，不访问网络。

复算输入来自原件 CSV/XML/ZIP/API JSON，而不是 reference.inputs 的镜像。
计算一致、原字节哈希一致、首次发布版本可证明，是三个独立结论。
"""
from __future__ import annotations

import argparse
import csv
import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import platform
import re
import shlex
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "datasets/agenthon-t4-reference"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode())


def near(a, b, tolerance=1e-8):
    return isinstance(a, (int, float)) and not isinstance(a, bool) and math.isfinite(a) \
        and math.isclose(a, b, rel_tol=1e-10, abs_tol=tolerance)


def half_up(value, digits):
    return float(Decimal(str(value)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def only(rows, message):
    if len(rows) != 1:
        raise ValueError(f"{message}：匹配 {len(rows)} 行，应为 1 行")
    return rows[0]


def visible_html_text(payload):
    class Visible(HTMLParser):
        def __init__(self):
            super().__init__(); self.hidden = 0; self.parts = []

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.hidden += 1

        def handle_endtag(self, tag):
            if tag in ("script", "style") and self.hidden:
                self.hidden -= 1

        def handle_data(self, value):
            if not self.hidden:
                self.parts.append(value)

    parser = Visible(); parser.feed(payload)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def chapter11_notice_date(text, company):
    """限定本次四个SEC原始8-K的已完成申请句式，不推断一般信用事件。"""
    pattern = (r"On\s+(?P<date>[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
               r".{0,90}?" + company +
               r".{0,400}?\bfiled\s+(?:a\s+)?voluntary\s+petitions?"
               r".{0,100}?\bchapter\s+11\b")
    dates = {datetime.strptime(re.sub(r",?\s+(\d{4})$", r", \1", m.group("date")),
                               "%B %d, %Y").date().isoformat()
             for m in re.finditer(pattern, text, re.I)}
    return only(sorted(dates), "SEC正文已完成Chapter11申请日期")


def earnings_source_dates(sources):
    """区分本次已登记来源的日期角色；声明日期不等同首发时点证明。"""
    dates = {key: set() for key in (
        "declared_release_dates", "declared_schedule_notice_dates",
        "declared_filing_dates", "declared_presentation_dates",
        "declared_other_source_dates")}
    for source in sources:
        published = source.get("published_at")
        if not published:
            continue
        title = source.get("title", "").casefold()
        url = source.get("url", "").casefold()
        if ("webcast" in title and "announc" in title) or "announces-webcast" in url:
            role = "declared_schedule_notice_dates"
        elif re.search(r"\bform\s+10-[qk]\b", title):
            role = "declared_filing_dates"
        elif "earnings presentation" in title:
            role = "declared_presentation_dates"
        elif "results" in title and ("reports" in title or "delivers" in title):
            role = "declared_release_dates"
        else:
            role = "declared_other_source_dates"
        dates[role].add(published)
    return {key: sorted(values) for key, values in dates.items()}


def pdf_ascii_text(path):
    """限用于本次保留 ASCII literal/TJ 的 Treasury PDF；不是通用 PDF/OCR。

    直接解压原 PDF Flate stream 并连接 literal tokens；无法解码的文件
    返回空文本，调用方必须明确记录限制，不从 reference locator 填补。
    """
    texts = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", Path(path).read_bytes(), re.S):
        try:
            body = zlib.decompress(match.group(1)).decode("latin1")
        except (zlib.error, UnicodeDecodeError):
            continue
        for literal in re.findall(r"\[((?:[^\]]|\\\])+?)\]\s*TJ", body):
            tokens = re.findall(r"\(((?:[^()\\]|\\.)*)\)", literal)
            line = "".join(re.sub(r"\\([()\\])", r"\1", x) for x in tokens)
            if line:
                texts.append(line)
    return "\n".join(texts)


class Auditor:
    def __init__(self, data):
        self.data = Path(data).resolve()
        self.sources = self.data / "sources"
        self.files = {}
        self.url_files = {}
        self.declared_missing = []
        self.used = set()
        self.cache = {}
        self.supplements = []
        self.supplement_errors = []
        self.index_evidence()

    def rel(self, path):
        path = Path(path).resolve()
        try:
            return str(path.relative_to(self.data))
        except ValueError:
            return str(path)

    def register(self, path, url=None, expected_sha=None, basis=None, upstream_sha=None):
        path = Path(path)
        relative = self.rel(path)
        if not path.exists():
            item = {"path": relative, "url": url, "expected_sha256": expected_sha,
                    "status": "原件未保存，无法回读哈希", "basis": basis}
            if item not in self.declared_missing:
                self.declared_missing.append(item)
            return
        entry = self.files.setdefault(relative, {
            "path": relative, "bytes": path.stat().st_size,
            "actual_sha256": sha_bytes(path.read_bytes()), "declarations": [], "urls": []})
        if url and url not in entry["urls"]:
            entry["urls"].append(url)
            self.url_files.setdefault(url, []).append(relative)
        decl = {"expected_sha256": expected_sha, "hash_match": None if expected_sha is None else
                expected_sha == entry["actual_sha256"], "basis": basis}
        if upstream_sha:
            decl["unverified_upstream_response_sha256"] = upstream_sha
        if decl not in entry["declarations"]:
            entry["declarations"].append(decl)

    def index_evidence(self):
        # 将全部保存文件做指纹；只有存在原先声明 hash 才称 hash_match=True。
        for path in sorted(self.sources.rglob("*")):
            if path.is_file():
                self.register(path, basis="本次离线指纹；没有既有哈希时不构成下载完整性证明")
        for path in self.sources.rglob("*.metadata.json"):
            m = read_json(path)
            target = path.parent / m.get("evidence_file", m.get("raw_path", path.name.removesuffix(".metadata.json")))
            self.register(target, m.get("url"), m.get("sha256", m.get("source_sha256")), f"{self.rel(path)} 下载元数据")
        macro = self.sources / "macro"
        for filename, field in [("alfred-downloads.json", "path"), ("release-downloads.json", "filename")]:
            for m in read_json(macro / filename):
                self.register(macro / m[field], m.get("url"), m.get("sha256"), filename)
        for m in read_json(self.sources / "cot/downloads.json"):
            self.register(self.sources / "cot" / m["path"], m.get("url"), m.get("sha256"),
                          f"COT downloads.json；{m.get('byte_form', '')}")
        earnings = self.sources / "earnings-credit"
        for path in earnings.glob("*.json"):
            m = read_json(path)
            if not isinstance(m, dict) or not m.get("url"):
                continue
            if m.get("raw_path"):
                raw = earnings / m["raw_path"]
                self.register(raw, m["url"], m.get("source_sha256"),
                              f"{path.name} 指向的完整原始响应")
            else:
                # companyfacts 过滤副本不是完整响应，绝不拿它匹配 source_sha256。
                self.register(path, m["url"], basis="结构化过滤快照或包装副本；上游 blob 未附",
                              upstream_sha=m.get("source_sha256"))
        metadata = earnings / "credit-primary-document-metadata.json"
        if metadata.exists():
            for m in read_json(metadata):
                local = m.get("path") or m.get("raw_path")
                if local:
                    self.register(earnings / local, m.get("url"), m.get("source_sha256"), metadata.name)
                else:
                    self.declared_missing.append({"path": None, "url": m.get("url"),
                        "expected_sha256": m.get("source_sha256"), "status": "仅保存正文下载元数据，正文未保留",
                        "basis": metadata.name})
        manifest = read_json(self.data / "inputs/source-manifest.json")
        for unit in manifest["units"]:
            for entry in unit["files"]:
                self.register(self.data / "inputs" / entry["path"], expected_sha=entry["sha256"],
                              basis="固定官方 commit 输入 manifest")
        for entry in manifest.get("license_files", []) + manifest.get("schemas", []):
            self.register(self.data / "inputs" / entry["path"], expected_sha=entry["sha256"],
                          basis="固定官方 commit 输入 manifest")
        self.index_supplement_evidence()
        # 补证若确实恢复了旧声明的完全相同字节，回读旧hash并移除“正文未保存”。
        remaining_missing = []
        for missing in self.declared_missing:
            matches = [self.files[p] for p in self.url_files.get(missing.get("url"), [])
                       if missing.get("expected_sha256") and
                       self.files[p]["actual_sha256"] == missing["expected_sha256"]]
            if missing.get("path") is None and matches:
                for entry in matches:
                    self.register(self.data / entry["path"], missing["url"],
                                  missing["expected_sha256"], "补证恢复的旧正文下载声明")
            else:
                remaining_missing.append(missing)
        self.declared_missing = remaining_missing

    def index_supplement_evidence(self):
        """回读补证清单的实际字节；清单内研究结论不代替独立公式审校。"""
        for path in sorted(self.sources.rglob("evidence-manifest.json")):
            manifest = read_json(path)
            if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
                self.supplement_errors.append({"manifest": self.rel(path),
                    "error": "补证清单必须为含sources数组的JSON对象"})
                continue
            preserved = 0
            for source in manifest.get("sources", []):
                if not isinstance(source, dict):
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "error": "补证sources条目必须为JSON对象"})
                    continue
                if source.get("status") != "downloaded":
                    continue
                relative = source.get("path")
                expected = source.get("sha256")
                if not isinstance(relative, str) or not relative or not isinstance(expected, str) \
                        or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "error": "已下载补证缺少相对路径或有效SHA-256"})
                    continue
                base = self.data if source.get("path_base") == "dataset" else path.parent.resolve()
                target = (base / relative).resolve()
                if source.get("path_base") not in (None, "dataset") or Path(relative).is_absolute() or ".." in Path(relative).parts or not target.is_relative_to(base):
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "error": "补证路径超出对应来源目录"})
                    continue
                if target.exists() and not target.is_file():
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "path": relative, "error": "补证路径必须是文件"})
                    continue
                self.register(target, source.get("url"), expected,
                              f"{self.rel(path)} 保存补证字节清单；{source.get('sanitization', '下载保存字节')}",
                              upstream_sha=source.get("download_sha256") if source.get("sanitization") else None)
                if not target.is_file():
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "path": relative, "error": "声明已下载补证正文缺失"})
                elif source.get("bytes") != target.stat().st_size:
                    self.supplement_errors.append({"manifest": self.rel(path),
                        "path": relative, "error": "补证字节数与下载声明不符"})
                else:
                    preserved += 1
            self.supplements.append({"manifest": self.rel(path),
                "manifest_sha256": sha_bytes(path.read_bytes()),
                "preserved_source_count": preserved,
                "research_checks": manifest.get("checks", []),
                "limitations": manifest.get("limitations", []),
                "scope": "仅下载声明与保存字节复核；research_checks为研究记录，不计作本工具独立公式复算"})

    def evidence(self, path, locator):
        path = Path(path)
        relative = self.rel(path)
        self.used.add(relative)
        if relative not in self.files:
            self.register(path, basis="计算时读取")
        item = self.files[relative]
        return {"path": relative, "sha256": item["actual_sha256"], "locator": locator,
                "declared_hash_matches": [d["hash_match"] for d in item["declarations"]
                                          if d["expected_sha256"] is not None]}

    def csv_value(self, series, vintage, obs):
        path = self.sources / "macro" / f"{series}_{vintage}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            column = f"{series}_{vintage.replace('-', '')}"
            if reader.fieldnames != ["observation_date", column]:
                raise ValueError(f"vintage 列名不匹配：{path.name} {reader.fieldnames}")
            rows = list(reader)
        value = float(only([r for r in rows if r["observation_date"] == obs], f"{path.name}/{obs}")[column])
        return value, self.evidence(path, f"observation_date={obs}; column={column}")

    def yield_vintage_value(self, series, observation):
        """直接回读观察日相邻三个ALFRED vintage，不使用派生comparison摘要。"""
        day = date.fromisoformat(observation)
        probes = []
        evidence = []
        for offset in (-1, 0, 1):
            vintage = (day + timedelta(days=offset)).isoformat()
            start = (day - timedelta(days=7)).isoformat()
            path = self.sources / "yield-vintages" / f"{series}_window-{start}_{observation}_vintage-{vintage}.csv"
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                column = f"{series}_{vintage.replace('-', '')}"
                if reader.fieldnames != ["observation_date", column]:
                    raise ValueError(f"收益率补证vintage列不符：{path.name}")
                matches = [r for r in reader if r["observation_date"] == observation and r[column] not in ("", ".")]
            if len(matches) > 1:
                raise ValueError(f"收益率目标日期重复：{path.name}")
            value = float(matches[0][column]) if matches else None
            probes.append({"vintage": vintage, "target_present": bool(matches), "value": value})
            evidence.append(self.evidence(path, f"observation_date={observation}; column={column}; 直接核对是否包含目标日"))
        if probes[0]["target_present"] or probes[1]["target_present"] or not probes[2]["target_present"]:
            raise ValueError(f"收益率相邻日可用性与本次证据预期不符：{series}/{observation}")
        return probes[2]["value"], probes, evidence

    def treasury_curve(self, year):
        key = ("curve", year)
        if key not in self.cache:
            path = self.sources / "treasury" / f"yield_curve_{year}.xml"
            d = "{http://schemas.microsoft.com/ado/2007/08/dataservices}"
            m = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"
            records = []
            for node in ET.parse(path).getroot().iter(m + "properties"):
                records.append({child.tag.removeprefix(d): child.text for child in node})
            self.cache[key] = records
        return self.cache[key]

    def cot_rows(self):
        if "cot" not in self.cache:
            p = self.sources / "cot"
            api = read_json(p / "legacy-futures-only-20241022-20241126.json")
            with zipfile.ZipFile(p / "deacot2024.zip") as z:
                annual = list(csv.DictReader(io.StringIO(z.read("annual.txt").decode("utf-8-sig"))))
            self.cache["cot"] = api, annual
        return self.cache["cot"]

    def eps_observations(self, symbol):
        p = self.sources / "earnings-credit"
        concept = p / f"sec-eps-{symbol}-concept.raw.json"
        if concept.exists():
            doc = read_json(concept)
            if doc["taxonomy"] != "us-gaap" or doc["tag"] != "EarningsPerShareDiluted":
                raise ValueError("SEC 单指标 taxonomy/tag 不符合 GAAP diluted EPS")
            return doc["units"]["USD/shares"], self.evidence(concept,
                "taxonomy=us-gaap; tag=EarningsPerShareDiluted; units.USD/shares"), "完整公开 companyconcept 响应"
        snapshot = p / f"sec-eps-{symbol}-filtered.json"
        doc = read_json(snapshot)
        if (doc["taxonomy"], doc["tag"], doc["unit"]) != ("us-gaap", "EarningsPerShareDiluted", "USD/shares"):
            raise ValueError("SEC 过滤快照 taxonomy/tag/unit 不符合 GAAP diluted EPS")
        return doc["selected_observations"], self.evidence(snapshot,
            "selected_observations; GAAP EarningsPerShareDiluted; 上游完整 blob 不在此副本"), "过滤快照，完整上游 blob 未保留"

    def bounded_credit_checks(self, symbol, task):
        """回读有限核查原文锚点和全窗名册；不将无命中称为穷尽证明。"""
        base = self.sources / "credit-resolution"
        report = read_json(base / "resolution-checks.json")
        record = only([r for r in report["records"] if r["entity_id"] == symbol], "信用有限验收实体")
        scope = record["acceptance_scope"]
        result = {"finite_scope_window_matches_task": scope["window_start_inclusive"] == "2023-04-01"
                  and scope["window_end_inclusive"] == task["resolution_date"],
                  "finite_scope_limits_preserved": bool(scope["limitations"])
                  and scope["court_check_status"] == "incomplete_access_403_not_zero_results"
                  and scope["official_private_outcome_verified"] is False
                  and scope["broader_all_subsidiary_scope_verified"] is False}
        for check in report["checks"]:
            if check.get("entity_id") != symbol or check["kind"] not in {"body_regex_anchor", "SEC_filing_roster"}:
                continue
            path = (base / check["path"]).resolve()
            if not path.is_relative_to(self.data) or path.is_symlink():
                raise ValueError("信用原文锚点路径越界")
            result[check["check_id"] + "_raw_hash"] = sha_bytes(path.read_bytes()) == check["sha256"]
            if check["kind"] == "body_regex_anchor":
                text = visible_html_text(path.read_text(encoding="utf-8"))
                result[check["check_id"] + "_original_anchor"] = bool(re.search(check["regex"], text, re.I | re.S))
            else:
                recent = read_json(path)["filings"]["recent"]
                actual = {a for a, d, f in zip(recent["accessionNumber"], recent["filingDate"], recent["form"])
                          if "2023-04-01" <= d <= task["resolution_date"] and f in {"10-K", "10-Q", "8-K", "8-K/A"}}
                result[check["check_id"] + "_roster_recalculated"] = actual == set(check["accession_numbers"])
        return result, scope

    @staticmethod
    def quarter(observations, intended_end):
        end = date.fromisoformat(intended_end)
        choices = []
        for obs in observations:
            if not obs.get("start") or obs.get("form") not in ("10-Q", "10-K"):
                continue
            actual_end = date.fromisoformat(obs["end"])
            duration = (actual_end - date.fromisoformat(obs["start"])).days
            if abs((actual_end - end).days) <= 7 and 75 <= duration <= 105:
                choices.append(obs)
        if not choices:
            return None, []
        choices.sort(key=lambda x: (x["filed"], x.get("accn", "")))
        return choices[0], choices

    def yahoo(self, symbol):
        p = self.sources / "earnings-credit" / f"yahoo-{symbol}-20240201-20240202.raw.json"
        result = only(read_json(p)["chart"]["result"], f"Yahoo {symbol} result")
        if result["meta"]["symbol"] != symbol:
            raise ValueError("Yahoo symbol 不匹配")
        tz = ZoneInfo(result["meta"]["exchangeTimezoneName"])
        by_date = {}
        quotes = result["indicators"]["quote"][0]["close"]
        adjusted = result["indicators"]["adjclose"][0]["adjclose"]
        for i, timestamp in enumerate(result["timestamp"]):
            local = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(tz)
            day = local.date().isoformat()
            if day in by_date:
                raise ValueError("同交易日出现重复日线")
            by_date[day] = {"timestamp": timestamp, "local_bar_timestamp": local.isoformat(),
                            "close_raw": quotes[i], "close_cent": half_up(quotes[i], 2),
                            "adjclose": adjusted[i]}
        return by_date, result.get("events", {}), self.evidence(p,
            "chart.result[0]; timestamp -> America/New_York 交易日期；日线 timestamp 为开盘锚点，close 为整日日线收盘")

    def ir_display_prices(self, symbol):
        names = {"AAPL": "apple-ir-history.json", "AMZN": "amazon-ir-feed.json",
                 "META": "meta-ir-history.json", "SPY": "spy-tickertech-proxy.json"}
        path = self.sources / "postearn-supplement" / names[symbol]
        rows = read_json(path)["GetStockQuoteHistoricalListResult"]
        by_date = {}
        for row in rows:
            # HistoricalDate是显示日期字段，不能把午夜/06:00当实际撮合或收盘时间。
            day = datetime.strptime(row["HistoricalDate"].split()[0], "%m/%d/%Y").date().isoformat()
            value = row["Last"]
            if day in by_date or not near(value, value) or value <= 0:
                raise ValueError("第二展示渠道日期重复或Last价格非法")
            by_date[day] = half_up(value, 2)
        if set(by_date) != {"2024-02-01", "2024-02-02"}:
            raise ValueError("第二展示渠道交易日期集合不符")
        return by_date, self.evidence(path, "HistoricalDate显示日期 / Last收盘展示字段；响应标的身份与上游独立性另有限制")

    def calculate(self, row, task, entity):
        tid = row["task_id"]
        result = {"computed_value": None, "computed_label": None, "formula": None,
                  "independent_inputs": [], "evidence": [], "checks": {}, "findings": [],
                  "proof_complete": False, "provenance_class": "source_annotation_only", "first_publication_status": "未证明",
                  "date_semantics": {"cutoff_date": task["cutoff_date"], "resolution_date": task["resolution_date"]}}
        ev, checks, findings = result["evidence"], result["checks"], result["findings"]
        if tid == "t4-cpicomp-202410-us11":
            series, vintage = entity["series_fred"], entity["release_date"]
            octdate = entity["ref_month"] + "-01"
            sep, e1 = self.csv_value(series, vintage, "2024-09-01")
            octv, e2 = self.csv_value(series, vintage, octdate)
            ev.extend([e1, e2]); value = 100 * (octv / sep - 1)
            result.update(computed_value=value, formula="100 * (October_SA_index / September_SA_index - 1)",
                independent_inputs=[{"series_id": series, "vintage": vintage, "September": sep, "October": octv}],
                first_publication_status="发布日 ALFRED 历史 vintage；指数推算值，不等于未舍入官方环比",
                provenance_class="designated_historical_vintage", proof_complete=True)
            checks["correct_release_vintage"] = vintage == "2024-11-13" and vintage > task["cutoff_date"]
            display = read_json(self.sources / "macro/release-evidence.json")["cpi"]["rounded_mom_pct"][row["entity_id"]]
            checks["rounded_to_BLS_release_display"] = near(half_up(value, 1), display)
            result["independent_inputs"].append({"BLS_browser_read_display_annotation": display,
                "basis": "先前官方网页查核的摘录；403 HTML 原件未保存，本次仅作辅助对照"})
            result["date_semantics"].update(ref_month=entity["ref_month"], release_date=vintage)
            findings.append("BLS 首稿环比仅一位小数；此值由三位小数发布日指数计算，评分器精度未知。")
        elif tid == "t4-macrorev-20240930-us6":
            series, obs = entity["series_id"], entity["ref_month"] + "-01"
            before, eb = self.csv_value(series, entity["latest_precutoff_vintage"], obs)
            after, ea = self.csv_value(series, entity["resolving_release_date"], obs)
            ev.extend([eb, ea]); delta = after - entity["latest_precutoff_estimate"]
            label = "up" if delta > 0 else "down" if delta < 0 else None
            result.update(computed_value=after, computed_label=label,
                formula="label = sign(resolving_vintage_level - task.latest_precutoff_estimate); reference_value = resolving_vintage_level",
                independent_inputs=[{"series_id": series, "ref_month": entity["ref_month"],
                    "baseline_vintage": entity["latest_precutoff_vintage"], "baseline_csv_level": before,
                    "task_baseline": entity["latest_precutoff_estimate"],
                    "resolving_vintage": entity["resolving_release_date"], "resolving_csv_level": after, "delta": delta}],
                first_publication_status="指定 resolving_release_date 的 ALFRED 历史 vintage；不是该月份首次估计",
                provenance_class="designated_historical_vintage", proof_complete=True)
            checks["baseline_equals_task"] = near(before, entity["latest_precutoff_estimate"])
            checks["baseline_precutoff_and_resolution_postcutoff"] = entity["latest_precutoff_vintage"] <= task["cutoff_date"] < entity["resolving_release_date"]
            checks["resolving_date_within_task_resolution"] = entity["resolving_release_date"] <= task["resolution_date"]
            checks["non_tie_label_defined"] = label is not None
            result["date_semantics"].update(ref_month=entity["ref_month"], resolving_release_date=entity["resolving_release_date"],
                observation_month_kept_separate_from_vintage=True)
            if series == "PI":
                release = entity["resolving_release_date"].replace("-", "")
                p = self.sources / "macro" / f"bea-pi-{release}.xlsx"
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                with zipfile.ZipFile(p) as archive:
                    ss = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                    strings = ["".join(n.itertext()) for n in ss.findall("s:si", ns)]
                    sheet = ET.fromstring(archive.read("xl/worksheets/sheet2.xml"))
                    h6 = only(sheet.findall(".//s:c[@r='H6']", ns), "BEA H6")
                    h7 = only(sheet.findall(".//s:c[@r='H7']", ns), "BEA H7")
                    header = strings[int(h6.find("s:v", ns).text)]
                    level = float(h7.find("s:v", ns).text)
                ev.append(self.evidence(p, f"sheet2 H6={header}; H7={level}"))
                checks["BEA_archived_workbook_equals_vintage"] = near(after, level)
            findings.append("同一月份不同 resolving vintage 单独审计；Development 本题 interval 官方不评分，不能把 level 当官方 numeric truth。")
        elif tid.startswith("t4-fomc-curve-"):
            start, end = entity["as_of"], task["resolution_date"]
            curve = self.treasury_curve(start[:4]); field = f"BC_{entity['maturity_years']}YEAR"
            s = float(only([x for x in curve if x["NEW_DATE"][:10] == start], "Treasury 起点")[field])
            e = float(only([x for x in curve if x["NEW_DATE"][:10] == end], "Treasury 终点")[field])
            result.update(computed_value=100 * (e - entity["start_yield_pct"]),
                formula="100 * (end_CMT_yield_pct - task.start_yield_pct)",
                independent_inputs=[{"field": field, "start_date": start, "official_start_pct": s,
                    "task_start_pct": entity["start_yield_pct"], "end_date": end, "official_end_pct": e}],
                first_publication_status="当前 Treasury 历史 XML；原历史版本修订链未证明",
                provenance_class="current_historical_series_unknown_vintage")
            checks["task_start_matches_official"] = near(s, entity["start_yield_pct"])
            checks["window_start_matches_cutoff"] = start == task["cutoff_date"]
            ev.append(self.evidence(self.sources / "treasury" / f"yield_curve_{start[:4]}.xml", f"NEW_DATE={start}/{end}; {field}"))
            findings.append("名义 CMT/par yield 为百分数，乘100后才是基点；XML 当前版本的 <updated> 不能当历史发布日期。")
            if (self.sources / "yield-vintages/evidence-manifest.json").is_file():
                vs, start_probes, es = self.yield_vintage_value(entity["series_fred"], start)
                ve, end_probes, ee = self.yield_vintage_value(entity["series_fred"], end)
                checks["historical_start_matches_task_and_XML"] = near(vs, s) and near(vs, entity["start_yield_pct"])
                checks["historical_end_matches_XML"] = near(ve, e)
                result.update(computed_value=100 * (ve - entity["start_yield_pct"]),
                              provenance_class="designated_historical_vintage", proof_complete=True,
                              first_publication_status="观察日前一日/当日ALFRED缺目标；次日vintage有目标值，全球原始源首次发布时间未证明")
                result["independent_inputs"].append({"ALFRED_start_probes": start_probes,
                                                   "ALFRED_end_probes": end_probes})
                result["date_semantics"].update(ALFRED_available_start_vintage=start_probes[-1]["vintage"],
                                              ALFRED_available_end_vintage=end_probes[-1]["vintage"],
                                              global_source_first_publication_proven=False)
                ev.extend(es + ee)
                findings.append("指定历史vintage数值已回读；ALFRED可见日期、观察日期和Treasury全球首发时点分别记录，不等同。")
        elif tid == "t4-auction-btc-202411-us7":
            day = entity["auction_date"]
            p = self.sources / "treasury" / f"auction_treasurydirect_{day}.json"
            a = only([x for x in read_json(p) if x["auctionDate"][:10] == day and
                x["securityTerm"] == entity["tenor"] and x["reopening"] == "No" and x["tips"] == "No"], "Treasury 拍卖")
            tendered = int(a["totalTendered"]) - int(a["somaTendered"])
            accepted = int(a["totalAccepted"]) - int(a["somaAccepted"])
            ratio = tendered / accepted; value = half_up(ratio, 2)
            fpath = self.sources / "treasury/auction_fiscaldata_202411.json"
            f = only([x for x in read_json(fpath)["data"] if x["auction_date"] == day and x["cusip"] == a["cusip"]], "FiscalData 拍卖")
            pdf = self.sources / "treasury" / a["pdfFilenameCompetitiveResults"]
            text = pdf_ascii_text(pdf)
            match = re.search(r"Bid-to-Cover Ratio:\s*\$([\d,]+)/\$([\d,]+)\s*=\s*([\d.]+)", text)
            if match:
                pt, pa, pr = int(match[1].replace(",", "")), int(match[2].replace(",", "")), float(match[3])
                checks["original_PDF_subtotal_matches_API"] = (pt, pa) == (tendered, accepted)
                checks["original_PDF_ratio_matches_recalculation"] = near(pr, value)
                checks["PDF_CUSIP_matches_API"] = a["cusip"] in text
                checks["PDF_printed_release_date_matches_auction"] = datetime.strptime(day, "%Y-%m-%d").strftime("%B %d, %Y") in text
                result["proof_complete"] = True
                result["provenance_class"] = "dated_original_release_document"
                result["first_publication_status"] = "拍卖日原始结果 PDF；API 当前响应作交叉核对"
                ev.append(self.evidence(pdf, f"直接解压 PDF TJ 文本，脚注 Bid-to-Cover Ratio: ${pt}/${pa}={pr}"))
            else:
                findings.append("原 PDF 已保存但本次有限 ASCII 解码失败；未从 reference.inputs 代填 PDF 数值。")
                result["first_publication_status"] = "当前 API 与已保存 PDF；PDF 数值未自动解码"
            checks["official_API_ratio_matches_recalculation"] = near(float(a["bidToCoverRatio"]), value)
            checks["FiscalData_ratio_matches"] = near(float(f["bid_to_cover_ratio"]), value)
            checks["FiscalData_subtotal_matches"] = (int(f["total_tendered"]) - int(f["soma_tendered"]),
                int(f["total_accepted"]) - int(f["soma_accepted"])) == (tendered, accepted)
            checks["new_coupon_auction"] = entity["new_or_reopening"] == "new" and a["securityType"] in ("Note", "Bond")
            checks["auction_date_within_resolution"] = task["cutoff_date"] < day <= task["resolution_date"]
            ev.extend([self.evidence(p, f"auctionDate={day}; cusip={a['cusip']}; SOMA 从 total 剔除"),
                       self.evidence(fpath, f"auction_date={day}; cusip={a['cusip']}；total-soma")])
            result.update(computed_value=value, formula="round_half_up((totalTendered-somaTendered)/(totalAccepted-somaAccepted), 2)",
                independent_inputs=[{"auction_date": day, "CUSIP": a["cusip"], "issueDate": a["issueDate"],
                    "subtotal_tendered": tendered, "subtotal_accepted": accepted,
                    "unrounded_ratio": ratio, "published_ratio": float(a["bidToCoverRatio"])}])
            result["date_semantics"].update(auction_date=day, match_on_issue_date=False)
        elif tid == "t4-cotpos-202411-us10":
            api, annual = self.cot_rows()
            s = only([x for x in api if x["report_date_as_yyyy_mm_dd"].startswith("2024-10-22") and
                      int(x["open_interest_all"]) == entity["open_interest_20241022"] and
                      int(x["noncomm_positions_long_all"]) - int(x["noncomm_positions_short_all"]) == entity["net_noncommercial_20241022"]], "COT 起始市场")
            code = s["cftc_contract_market_code"]
            e = only([x for x in api if x["report_date_as_yyyy_mm_dd"].startswith("2024-11-26") and x["cftc_contract_market_code"] == code], "COT 结束市场")
            triples = []
            for x in [s, e]:
                day = x["report_date_as_yyyy_mm_dd"][:10]
                a = only([x for x in annual if x["As of Date in Form YYYY-MM-DD"].strip() == day and
                          x["CFTC Contract Market Code"].strip() == code], "COT annual 原始行")
                keys = [("noncomm_positions_long_all", "Noncommercial Positions-Long (All)"),
                        ("noncomm_positions_short_all", "Noncommercial Positions-Short (All)"),
                        ("open_interest_all", "Open Interest (All)")]
                checks[f"annual_API_equal_{day}"] = all(int(x[k]) == int(a[col]) for k, col in keys)
                triples.append({"date": day, "long": int(a[keys[0][1]]), "short": int(a[keys[1][1]]), "OI": int(a[keys[2][1]])})
            sn, en = triples[0]["long"] - triples[0]["short"], triples[1]["long"] - triples[1]["short"]
            value = 100 * (en - sn) / triples[0]["OI"]
            result.update(computed_value=value, formula="100 * ((end_noncommercial_long-end_short) - (start_long-start_short)) / start_open_interest",
                independent_inputs=[{"market_code": code, "market": s["market_and_exchange_names"], "observations": triples}],
                first_publication_status="当前 CFTC 年度文件/API；首次发布修订链未知",
                provenance_class="current_historical_series_unknown_vintage")
            ev.extend([self.evidence(self.sources / "cot/deacot2024.zip", f"annual.txt; code={code}; dates=2024-10-22/2024-11-26"),
                self.evidence(self.sources / "cot/legacy-futures-only-20241022-20241126.json", f"code={code}; dates=2024-10-22/2024-11-26")])
            result["date_semantics"].update(start_report_as_of="2024-10-22", end_report_as_of="2024-11-26",
                dates_are_report_as_of_not_release_dates=True)
            findings.append("固定起始 OI 分母；两期 net/OI 百分比相减会产生另一指标。两份当前官方数据一致不证明 first publication。")
        elif tid in ("t4-EXAMPLE-eps-beat", "t4-eps-growth-2024Q3-banks", "t4-eps-yoy-2023Q2-mixed"):
            observations, evi, basis = self.eps_observations(row["entity_id"])
            intended = "2024-03-31" if tid == "t4-EXAMPLE-eps-beat" else re.search(r"\d{4}-\d{2}-\d{2}", entity["quarter_reported"])[0]
            actual, matches = self.quarter(observations, intended)
            if actual is None:
                raise ValueError("SEC 保存资料中无单季度 GAAP diluted EPS")
            value = float(actual["val"]); ev.append(evi)
            details = {"SEC_dataset_basis": basis, "intended_end": intended, "selected_original_filing_observation": actual,
                "same_quarter_distinct_values": sorted({float(x["val"]) for x in matches})}
            checks["single_quarter_duration"] = 75 <= (date.fromisoformat(actual["end"]) - date.fromisoformat(actual["start"])).days <= 105
            checks["GAAP_diluted_tag"] = True
            source_dates = earnings_source_dates(row["sources"])
            published = source_dates["declared_release_dates"]
            result["date_semantics"].update(quarter_start=actual["start"], quarter_end=actual["end"],
                first_selected_SEC_filed_date=actual["filed"], **source_dates,
                release_date_scope="按已登记来源标题/URL区分公告、预告、申报和演示；声明日期不自动证明首次发布",
                release_vs_resolution="release_after_resolution" if published and min(published) > task["resolution_date"] else "release_on_or_before_resolution" if published else "unknown")
            if tid == "t4-EXAMPLE-eps-beat":
                consensus, threshold = entity["consensus_eps"], entity["threshold_pct"]
                label = "beat" if value > consensus * (1 + threshold) else "miss" if value < consensus * (1 - threshold) else "inline"
                result.update(computed_value=value, computed_label=label,
                    formula="actual GAAP EPS > consensus*(1+threshold): beat; < consensus*(1-threshold): miss; else inline")
                details.update(consensus=consensus, threshold_fraction=threshold)
            else:
                prior_date = re.search(r"\d{4}-\d{2}-\d{2}", entity["prior_year_quarter"])[0]
                prior, _ = self.quarter(observations, prior_date)
                baseline = entity["prior_year_q_eps"]
                details.update(task_prior_year_q_eps=baseline, prior_observation=prior)
                if prior:
                    checks["prior_original_SEC_matches_task_baseline"] = near(prior["val"], baseline)
                else:
                    findings.append("保存 SEC 过滤快照未含 prior 同季观察值；公式以题面 baseline 为准，prior 披露未独立复核。")
                if tid == "t4-eps-growth-2024Q3-banks":
                    result.update(computed_value=100 * (value - baseline) / baseline,
                        formula="100 * (actual_single_quarter_GAAP_diluted_EPS - task.prior_year_q_eps) / task.prior_year_q_eps")
                    checks["positive_nonzero_task_baseline"] = baseline > 0
                else:
                    label = "up" if value > baseline else "down" if value < baseline else None
                    result.update(computed_value=value, computed_label=label,
                        formula="actual_single_quarter_GAAP_diluted_EPS > task.prior_year_q_eps: up; <: down")
                    checks["non_tie_label_defined"] = label is not None
            result["independent_inputs"].append(details)
            result["first_publication_status"] = "按原始申报 accession/filed 选单季观察值；业绩首稿正文未离线复核"
            result["provenance_class"] = "earliest_filing_xbrl_observation"
            findings.append("保存 SEC API 可复核 GAAP 单季数值与申报版本；10-Q 申报日不能替代首次 earnings 公告日。")
            if result["date_semantics"]["release_vs_resolution"] == "release_after_resolution":
                checks["late_release_kept_provisional"] = row["status"] == "provisional"
                findings.append("实际业绩公告晚于题面 resolution；预告网页日期不替代实际披露日，必须保持 provisional 并保留官方 outcome 日期口径歧义。")
        elif tid == "t4-postearn-20240201-megacap":
            # 重新运行原件审校，不把已保存报告的passed自述当作来源证明。
            import subprocess
            resolution_dir = self.sources / "postearn-resolution"
            resolution = read_json(resolution_dir / "normalized-evidence.json")
            verification = subprocess.run(
                [sys.executable, str(resolution_dir / "verify.py"),
                 "--source-root", str(self.data), "--full-report"],
                check=False, capture_output=True, text=True, timeout=30)
            if not verification.stdout.strip():
                raise ValueError("postearn 原件审校没有输出：" + verification.stderr[-500:])
            verified = json.loads(verification.stdout)
            checks["finite_window_original_evidence_reverified"] = (
                verification.returncode == 0 and verified.get("passed") is True
                and verified.get("verification_mode") == "local_originals_and_derived_values"
                and bool(verified.get("checks"))
                and all(c.get("pass") is True for c in verified["checks"]))
            checks["quality_fact_status_verified"] = row.get("quality", {}).get("fact_status") == "verified"
            checks["quality_task_semantics_aligned"] = row.get("quality", {}).get("task_alignment") == "aligned"
            checks["first_publication_separate_and_unknown"] = row.get("quality", {}).get("first_publication_status") == "unconfirmed"
            checks["official_outcome_alignment_not_claimed"] = row.get("quality", {}).get("official_outcome_status") == "unconfirmed"
            checks["verified_status_has_fact_evidence"] = row["status"] == "verified"
            stock, se, es = self.yahoo(row["entity_id"]); spy, be, eb = self.yahoo("SPY")
            days = ["2024-02-01", "2024-02-02"]
            checks["same_NY_trading_dates"] = set(stock) == set(spy) == set(days)
            def ret(data, column):
                return 100 * (data[days[1]][column] / data[days[0]][column] - 1)
            value = ret(stock, "close_cent") - ret(spy, "close_cent")
            adj = ret(stock, "adjclose") - ret(spy, "adjclose")
            raw = ret(stock, "close_raw") - ret(spy, "close_raw")
            threshold = entity["flat_threshold_abn_pct"]
            checks["task_threshold_is_one_percentage_point"] = threshold == 1
            def label(v):
                return "positive_reaction" if v > threshold else "negative_reaction" if v < -threshold else "flat"
            checks["close_adjusted_labels_equal"] = label(value) == label(adj)
            checks["vendor_reports_no_window_actions"] = not se and not be
            resolved = verified["returns"][row["entity_id"]]
            checks["independent_fraction_formula_matches_raw_prices"] = near(value, resolved["abnormal_return_percent"])
            checks["normalized_closes_match_original_prices"] = all(
                near(stock[d]["close_cent"], float(resolution["prices"][row["entity_id"]]["close_cents"][i]))
                and near(spy[d]["close_cent"], float(resolution["prices"]["SPY"]["close_cents"][i]))
                for i, d in enumerate(days))
            result.update(computed_value=value, computed_label=label(value),
                formula="100*(company_close_end/company_close_start - 1) - 100*(SPY_close_end/SPY_close_start - 1)",
                independent_inputs=[{"company": stock, "SPY": spy, "company_events": se, "SPY_events": be,
                    "cent_normalized_abnormal_pct": value, "raw_float_abnormal_pct": raw,
                    "adjusted_close_abnormal_pct": adj, "adjusted_minus_cent_difference_pp": adj - value,
                    "threshold_pct": threshold}, {"finite_window_resolution_facts": resolution["corporate_actions"],
                    "actual_original_check_count": verified["check_count"],
                    "actual_original_checks": verified["checks"],
                    "fraction_recalculation": resolved}],
                quality=row.get("quality", {}),
                proof_complete=checks["finite_window_original_evidence_reverified"],
                first_publication_status="当前 Yahoo 历史快照；first_publication=unknown，独立于本地事实复核",
                provenance_class="current_historical_series_finite_window_verified")
            ev.extend([es, eb]); result["date_semantics"].update(event_window=entity["event_window"],
                report_datetime=entity["report_datetime"], intraday_bar_timestamp_is_not_close_time=True)
            ev.append(self.evidence(resolution_dir / "normalized-evidence.json", "有限窗口派生事实；本次另回读完整原件，不以此文件代替原件"))
            findings.append("纽约历史时区使用 zoneinfo（2024年2月为 EST），不使用当前 meta.gmtoffset/EDT；2024-01-31 背景价不进入公式。")
            findings.append("官方card指定Yahoo日收盘；close已按拆股调整，Adj Close另含现金分配；指定窗口事件、原始除息表和SSGA分配表支持本地total return估计。")
            findings.append("公司行动证明范围限定本题两日；本地fact_status=verified不等同全球首发版本或主办方私有outcome已确认。")
            if (self.sources / "postearn-supplement/evidence-manifest.json").is_file():
                ir_stock, isrc = self.ir_display_prices(row["entity_id"])
                ir_spy, bsrc = self.ir_display_prices("SPY")
                checks["second_display_cent_prices_match_Yahoo"] = all(
                    near(ir_stock[d], stock[d]["close_cent"]) and near(ir_spy[d], spy[d]["close_cent"]) for d in days)
                result["independent_inputs"].append({"IR_display_company": ir_stock, "proxy_display_SPY": ir_spy,
                    "upstream_independence_proven": False, "SPY_response_symbol_metadata_present": False})
                ev.extend([isrc, bsrc])
                findings.append("第二展示渠道美分收盘一致，但同类Q4服务上游独立性未知；SPY标的来自请求，响应无symbol元数据，不能称交易所/SSGA官方收盘认证。")
        elif tid == "t4-credit-event-2023":
            details = {"window_start_exclusive": task["cutoff_date"], "window_end_inclusive": task["resolution_date"]}
            result["formula"] = "(cutoff, resolution] 内任一 Chapter 11/7、payment default 或被评级机构认定的 distressed exchange => credit_event"
            companies = {"BBBY": r"Bed Bath (?:and|&) Beyond", "RAD": r"Rite Aid Corporation",
                         "WE": r"WeWork Inc\.", "YELL": r"Yellow Corporation"}
            folder = self.sources / "credit-supplement/documents" / row["entity_id"]
            bodies = sorted(folder.glob("*8k.htm")) if row["entity_id"] in companies else []
            # 已保存的原始事件正文决定是否核查正例，不能让待审标签跳过真值证据。
            if not bodies and row["reference_label"] == "no_event":
                if row.get("quality", {}).get("fact_status") == "bounded_verified":
                    actual_checks, scope = self.bounded_credit_checks(row["entity_id"], task)
                    checks.update(actual_checks)
                    checks["bounded_scope_recorded_in_reference"] = bool(row["quality"].get("coverage_limits"))
                    checks["bounded_reference_task_aligned"] = row["quality"].get("task_alignment") == "aligned"
                    result["acceptance_scope"] = scope
                    result["provenance_class"] = "bounded_public_negative_case"
                    findings.append("按声明主体/窗口的公开SEC正文、债务合同和评级名册作有限验收；法院和保密/未评级资料缺口仍保留，不称无事件穷尽证明。")
                else:
                    checks["negative_case_kept_provisional"] = row["status"] == "provisional"
                    result["provenance_class"] = "negative_proof_incomplete"
                checks["negative_numeric_truth_not_invented"] = row["reference_value"] is None
                result["first_publication_status"] = "无事件不存在单一首发公告；有限公开检索，未覆盖所有保密/未评级/未披露事件"
            else:
                if bodies:
                    path = only(bodies, "该正例原始事件8-K")
                    event = chapter11_notice_date(visible_html_text(path.read_text(encoding="utf-8")), companies[row["entity_id"]])
                    details["event_date_from_original_SEC_body"] = event
                    checks["original_event_date_in_window"] = task["cutoff_date"] < event <= task["resolution_date"]
                    checks["reference_event_date_matches_original_body"] = any(
                        i["name"] == "chapter_11_filing_date" and i["value"] == event for i in row["inputs"])
                    result.update(computed_label="credit_event", proof_complete=True,
                                  provenance_class="dated_original_event_document")
                    checks["reference_label_matches_original_event"] = row["reference_label"] == result["computed_label"]
                    result["first_publication_status"] = "原始SEC8-K正文确认实际申请日期；申报日期单独记录，不声称最早全球公告版本"
                    ev.append(self.evidence(path, "Item 1.03；公司已filed voluntary petition(s) under Chapter 11的实际日期"))
                    findings.append("正文确认已完成申请，区分事件日期和8-K提交日；只证明该正例事件，不证明四个no_event的全窗无事件。")
                else:
                    event = next((i["value"] for i in row["inputs"] if i["name"] == "chapter_11_filing_date"), None)
                    details["event_date_from_prior_source_annotation"] = event
                    checks["annotated_event_date_in_window"] = bool(event) and task["cutoff_date"] < event <= task["resolution_date"]
                    result["first_publication_status"] = "有具日期的公开SEC事件公告定位；公告正文未保存为本次离线原件"
                    findings.append("此正例未保存正文，日期窗口只对先前摘录做一致性检查，不能称独立重新证明事件。")
                checks["positive_numeric_truth_not_invented"] = row["reference_value"] is None
            result["independent_inputs"].append(details)
        else:
            raise ValueError(f"未实现任务审校：{tid}")
        if result["computed_value"] is not None:
            checks["reference_value_matches_original_source_calculation"] = near(row["reference_value"], result["computed_value"])
            if row["target_type"] == "classification":
                checks["reference_label_matches_calculation"] = row["reference_label"] == result["computed_label"]
        return result

    def audit(self, reference, rows_override=None):
        manifest = read_json(self.data / "inputs/source-manifest.json")
        tasks = {u["task_id"]: read_json(self.data / "inputs" / u["task_path"]) for u in manifest["units"]}
        expected = {(t["task_id"], e["entity_id"]) for t in tasks.values() for e in t["entities"]}
        references = rows_override if rows_override is not None else [json.loads(line) for line in Path(reference).read_text().splitlines() if line.strip()]
        actual = [(r.get("task_id"), r.get("entity_id")) for r in references]
        structural = {"expected_tasks": len(tasks), "expected_rows": len(expected), "observed_rows": len(actual),
            "unique_keys": len(set(actual)) == len(actual), "exact_roster_match": set(actual) == expected,
            "missing_keys": [list(x) for x in sorted(expected - set(actual))],
            "extra_keys": [list(x) for x in sorted(set(actual) - expected)],
            "task_source_manifest_hashes_match": all(d["hash_match"] is not False for f in self.files.values()
                if f["path"].startswith("inputs/") for d in f["declarations"])}
        units = {u["task_id"]: u for u in manifest["units"]}
        audited = []
        for row in references:
            key = (row.get("task_id"), row.get("entity_id"))
            item = {"task_id": key[0], "entity_id": key[1], "reference_status": row.get("status"),
                    "reference_value": row.get("reference_value"), "reference_label": row.get("reference_label"), "checks": {}}
            checks = item["checks"]
            checks["key_in_official_roster"] = key in expected
            if key not in expected:
                item.update(pass_flag=False, findings=["参考记录不在固定官方 task roster 内"])
                audited.append(item); continue
            task = tasks[key[0]]; entity = only([x for x in task["entities"] if x["entity_id"] == key[1]], "任务实体")
            checks["target_type_matches_task"] = row.get("target_type") == task["target"]["type"]
            checks["task_canonical_sha256_matches"] = row.get("task_canonical_sha256") == canonical_sha(task) == units[key[0]]["task_canonical_sha256"]
            labels = task["target"].get("labels", [])
            checks["label_in_task_labels_or_null"] = row.get("reference_label") in labels if labels and row.get("status") != "unresolved" else row.get("reference_label") is None
            checks["valid_status"] = row.get("status") in ("verified", "provisional", "unresolved")
            checks["finite_numeric_value_or_null"] = near(row.get("reference_value"), row.get("reference_value", 0)) if row.get("reference_value") is not None else True
            expected_unit = entity.get("unit", entity.get("units"))
            if key[0].startswith("t4-eps-growth-") or key[0].startswith("t4-postearn-"):
                expected_unit = "percent"
            elif key[0] in ("t4-EXAMPLE-eps-beat", "t4-eps-yoy-2023Q2-mixed"):
                expected_unit = "USD/share"
            elif key[0] == "t4-credit-event-2023":
                expected_unit = "label"
            checks["unit_matches_target_semantics"] = row.get("unit") == expected_unit
            checks["method_and_notes_present"] = bool(row.get("method")) and bool(row.get("notes"))
            checks["source_url_title_locator_present"] = bool(row.get("sources")) and all(
                s.get("url", "").startswith("https://") and s.get("title") and s.get("locator") for s in row.get("sources", []))
            item["source_preservation"] = [{"url": s["url"], "locator": s["locator"],
                "local_files": sorted(set(self.url_files.get(s["url"], []))),
                "status": "已保存本地来源" if self.url_files.get(s["url"]) else
                    "固定官方 task 的本地副本" if "github.com/Agenthon-2026/" in s["url"] and s["url"].endswith("/task.json") else "仅 URL 与先前查核定位；本次无本地原正文"}
                for s in row.get("sources", [])]
            if row.get("status") == "unresolved":
                checks["unresolved_values_are_null"] = row.get("reference_value") is None and row.get("reference_label") is None
                item.update(computed_value=None, computed_label=None, findings=["原记录 unresolved：不代填未知真值；保留来源与后续核验路径。"],
                            proof_complete=False, provenance_class="unresolved", first_publication_status="未证明")
            else:
                try:
                    result = self.calculate(row, task, entity)
                    checks.update(result.pop("checks")); item.update(result)
                except (ValueError, KeyError, OSError, ET.ParseError, IndexError, TypeError) as error:
                    checks["original_source_read_and_calculation"] = False
                    item.update(computed_value=None, computed_label=None, findings=[f"原件读取或复算失败：{type(error).__name__}: {error}"],
                                proof_complete=False, provenance_class="audit_failed", first_publication_status="审校失败，无法判断")
            item["calculation_pass"] = checks.get("reference_value_matches_original_source_calculation")
            item["pass_flag"] = all(value is True for value in checks.values())
            audited.append(item)
        cot = [x for x in audited if x["task_id"] == "t4-cotpos-202411-us10" and x.get("computed_value") is not None]
        ranks = {x["entity_id"]: i + 1 for i, x in enumerate(sorted(cot, key=lambda x: x["computed_value"], reverse=True))}
        by_reference = {(x["task_id"], x["entity_id"]): x for x in references}
        for item in cot:
            item["computed_rank"] = ranks[item["entity_id"]]
            item["checks"]["rank_descending_largest_net_long_change"] = by_reference[(item["task_id"], item["entity_id"])].get("reference_rank") == item["computed_rank"]
            item["pass_flag"] = all(x is True for x in item["checks"].values())
        hash_failures = [{"path": f["path"], "actual_sha256": f["actual_sha256"], "declaration": d}
            for f in self.files.values() for d in f["declarations"] if d["hash_match"] is False]
        pass_flag = structural["unique_keys"] and structural["exact_roster_match"] and structural["task_source_manifest_hashes_match"] \
            and not hash_failures and not self.supplement_errors and all(r["pass_flag"] for r in audited)
        summary = {"records": len(audited), "tasks": len(tasks),
            "reference_status_counts": {s: sum(r["reference_status"] == s for r in audited) for s in ("verified", "provisional", "unresolved")},
            "row_integrity_pass": sum(r["pass_flag"] for r in audited),
            "independent_numeric_calculation_pass": sum(r.get("calculation_pass") is True for r in audited),
            "independent_numeric_calculation_fail": sum(r.get("calculation_pass") is False for r in audited),
            "no_independent_numeric_calculation": sum(r.get("calculation_pass") is None for r in audited),
            "independent_positive_credit_events_confirmed": sum(
                r.get("checks", {}).get("reference_label_matches_original_event") is True for r in audited),
            "designated_vintage_or_release_archive_supported": sum(r.get("proof_complete", False) for r in audited),
            "provenance_class_counts": {c: sum(r.get("provenance_class") == c for r in audited) for c in sorted({r.get("provenance_class", "audit_failed") for r in audited})},
            "hash_files_checked_against_prior_declaration": sum(any(d["expected_sha256"] for d in f["declarations"]) for f in self.files.values()),
            "hash_failures": len(hash_failures), "pass_flag": pass_flag,
            "supplement_manifest_count": len(self.supplements),
            "supplement_validation_errors": len(self.supplement_errors),
            "pass_flag_scope": "roster/字段/源哈希/已实现数值公式一致；不表示所有78行已证明首次发布或完整无事件",
            "fit_ready_without_additional_provenance": False}
        return {"schema_version": "0.1.0", "audited_at": datetime.now(timezone.utc).isoformat(),
            "mode": "offline_legally_acquired_sources", "official_outcome_compared": False,
            "environment": {"python_version": sys.version, "python_executable": Path(sys.executable).name,
                "platform": platform.platform(), "working_directory": "项目根目录",
                "command": "python3 tools/audit_reference_data.py --private-sources <本地证据缓存> --self-check",
                "script_sha256": sha_bytes(Path(__file__).read_bytes()), "third_party_dependencies": []},
            "input": {"reference_path": self.rel(reference), "reference_sha256": sha_bytes(Path(reference).read_bytes()),
                "source_manifest_sha256": sha_bytes((self.data / "inputs/source-manifest.json").read_bytes()),
                "source_commit": manifest["source_commit"]},
            "summary": summary, "roster_validation": structural,
            "material_findings": [
                "verified 是公开来源研究状态，不能自动视为 first-published provenance proof。",
                "CPI 使用发布日 vintage 指数；BLS 首稿显示0.1个百分点精度，派生值不等于官方内部未舍入值。",
                "宏观同月不同 resolving vintage 逐行保留；macrorev Development 官方 numeric truth 缺失，私有评分未比对。",
                "COT年度/API、Treasury曲线当前历史 XML 和 Yahoo 当前历史快照未提供完整首次发布修订链。",
                "EPS SEC 原始申报季度观察值与题面 prior 分开；过滤快照的 source_sha256 不是过滤副本字节哈希。",
                "收益率补证直接读取三个相邻历史vintage；ALFRED可见日不等于Treasury全球首发时点。",
                "补证清单内research_checks保持研究记录范围；脱敏副本hash只核对保存字节，不回读已删除的原始HTTP响应。",
                "AMGN 2023Q2 实际 earnings release 晚于 task resolution；维持 provisional 并保留 outcome 日期定义歧义。",
                "信用负例按有限公开核查范围验收；无事件非穷尽保证，不能把本次 pass_flag 解读为 proof complete。",
                "Yahoo 日线开盘 timestamp 只定位交易日，历史 NY 时区独立换算；无 vendor events 不等于完整公司行动证明。"],
            "hash_failures": hash_failures, "declared_but_unpreserved_sources": self.declared_missing,
            "supplementary_evidence": self.supplements,
            "supplement_validation_errors": self.supplement_errors,
            "file_inventory": [dict(f, used_in_independent_calculation=f["path"] in self.used) for f in sorted(self.files.values(), key=lambda f: f["path"])],
            "records": audited}


def negative_controls(auditor, reference):
    """仅在内存破坏参考记录，确认审校能拦截常见错值/错单位/错排名。

    不修改输入、不访问网络；不创建测试替代真值。每个 control
    单独从正式参考记录深拷贝，因此不会污染真实报告。
    """
    original = [json.loads(line) for line in Path(reference).read_text().splitlines() if line.strip()]
    controls = []
    cases = [
        ("CPI数值偏移", "t4-cpicomp-202410-us11", lambda r: r.update(reference_value=r["reference_value"] + 1), "reference_value_matches_original_source_calculation"),
        ("国债bps错单位", "t4-fomc-curve-20240918", lambda r: r.update(unit="percent"), "unit_matches_target_semantics"),
        ("COT反向排名", "t4-cotpos-202411-us10", lambda r: r.update(reference_rank=999), "rank_descending_largest_net_long_change"),
        ("EPS标签翻转", "t4-eps-yoy-2023Q2-mixed", lambda r: r.update(reference_label="up" if r["reference_label"] == "down" else "down"), "reference_label_matches_calculation"),
        ("信用标签伪造numerictruth", "t4-credit-event-2023", lambda r: r.update(reference_value=1.0), "positive_numeric_truth_not_invented"),
    ]
    if (auditor.sources / "credit-supplement/documents/BBBY").is_dir():
        def wrong_event_date(row):
            for value in row["inputs"]:
                if value["name"] == "chapter_11_filing_date":
                    value["value"] = "2023-04-24"
        cases.append(("信用事件日期混用申报日", "t4-credit-event-2023", wrong_event_date,
                      "reference_event_date_matches_original_body"))
        cases.append(("信用正例降为暂定负例", "t4-credit-event-2023",
                      lambda r: r.update(reference_label="no_event", status="provisional"),
                      "reference_label_matches_original_event"))
    for name, task_id, mutate, expected_check in cases:
        rows = copy.deepcopy(original)
        target = next(r for r in rows if r["task_id"] == task_id)
        mutate(target)
        report = auditor.audit(reference, rows)
        result = next(r for r in report["records"] if (r["task_id"], r["entity_id"]) == (task_id, target["entity_id"]))
        caught = result["checks"].get(expected_check) is False and report["summary"]["pass_flag"] is False
        controls.append({"name": name, "task_id": task_id, "entity_id": target["entity_id"],
                         "expected_failed_check": expected_check, "caught": caught})
    amgn = next((r for r in original if r["task_id"] == "t4-eps-yoy-2023Q2-mixed" and
                 r["entity_id"] == "AMGN"), None)
    if amgn:
        rows = copy.deepcopy(original)
        target = next(r for r in rows if r["task_id"] == amgn["task_id"] and r["entity_id"] == "AMGN")
        target["status"] = "verified"
        report = auditor.audit(reference, rows)
        result = next(r for r in report["records"] if r["task_id"] == target["task_id"] and r["entity_id"] == "AMGN")
        caught = result["checks"].get("late_release_kept_provisional") is False and not report["summary"]["pass_flag"]
        controls.append({"name": "AMGN预告掩盖实际延后披露", "task_id": target["task_id"], "entity_id": "AMGN",
                         "expected_failed_check": "late_release_kept_provisional", "caught": caught})
    return {"mode": "memory_only_negative_controls", "cases": controls, "pass_flag": all(x["caught"] for x in controls)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--private-sources", type=Path, help="仅本地的隔离原件缓存；相对路径与dataset一致，不公开原件")
    parser.add_argument("--self-check", action="store_true", help="内存注入参考错值、日期、单位、标签和状态错误；不改任何数据")
    args = parser.parse_args()
    dataset = args.dataset.resolve()
    reference = (args.reference or dataset / "reference.jsonl").resolve()
    output = (args.output or dataset / "qa/formula-audit.json").resolve()
    try:
        try:
            from tools.public_sources import materialized_dataset, SourceError
        except ModuleNotFoundError:
            from public_sources import materialized_dataset, SourceError
        with materialized_dataset(dataset, args.private_sources) as effective:
            effective_reference = effective / "reference.jsonl" if reference == dataset / "reference.jsonl" else reference
            auditor = Auditor(effective)
            report = auditor.audit(effective_reference)
            if args.self_check:
                report["negative_controls"] = negative_controls(auditor, effective_reference)
                report["summary"]["negative_controls_pass"] = report["negative_controls"]["pass_flag"]
                report["summary"]["pass_flag"] = report["summary"]["pass_flag"] and report["negative_controls"]["pass_flag"]
    except SourceError as exc:
        print(f"证据缓存校验失败：{exc}；请按public-source-catalog合法准备原件并指定--private-sources。", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    for row in report["records"]:
        if not row["pass_flag"]:
            print("FAIL", row["task_id"], row["entity_id"], [k for k, v in row["checks"].items() if not v])
    print(f"报告：{output}")
    return 0 if report["summary"]["pass_flag"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
