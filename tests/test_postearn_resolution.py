"""postearn 有限窗口审校的负例；使用生成的小型事实夹具，不联网或依赖私有原件。"""
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets/agenthon-t4-reference"
RESOLUTION = DATA / "sources/postearn-resolution"


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = module_from(ROOT / "tools/audit_reference_data.py", "postearn_auditor")
VERIFY = module_from(RESOLUTION / "verify.py", "postearn_verifier")


class PostearnResolutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = Path(temp.name)
        self.folder = self.data / "sources/postearn-resolution"
        self.folder.mkdir(parents=True)
        shutil.copyfile(RESOLUTION / "verify.py", self.folder / "verify.py")
        self.normalized = json.loads((RESOLUTION / "normalized-evidence.json").read_text())
        self.normalized["corporate_actions"]["SPY"]["full_table_spy_row_count"] = 2
        unit = "inputs/units/t4-postearn-20240201-megacap"
        for name in ("card.toml", "task.json"):
            path = self.data / unit / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DATA / unit / name, path)
        self.task = json.loads((self.data / unit / "task.json").read_text())
        self.entity = copy.deepcopy(next(e for e in self.task["entities"] if e["entity_id"] == "AAPL"))
        self.row = {"task_id": self.task["task_id"], "entity_id": "AAPL", "target_type": "classification",
                    "reference_value": self.normalized["resolution"]["AAPL"]["reference_value"],
                    "reference_label": "negative_reaction", "status": "verified",
                    "quality": copy.deepcopy(self.normalized["resolution"]["AAPL"]["quality"])}
        for symbol, price in self.normalized["prices"].items():
            raw = {"chart": {"result": [{"meta": price["meta"], "timestamp": price["timestamps"],
                   "indicators": {"quote": [{"close": price["close_float"]}],
                                  "adjclose": [{"adjclose": price["adjclose_float"]}]}}], "error": None}}
            stem = f"sources/earnings-credit/yahoo-{symbol}-20240201-20240202"
            self.write_json(stem + ".raw.json", raw)
            self.write_json(stem + ".json", {"url": "https://fixture.test/" + symbol,
                                           "response": raw, "raw_path": Path(stem + ".raw.json").name})
        for symbol, filename in (("AAPL", "apple-nasdaq-dividend.json"), ("META", "meta-nasdaq-dividend.json")):
            action = self.normalized["corporate_actions"][symbol]
            year, month, day = action["ex_date"].split("-")
            self.write_json("sources/postearn-supplement/" + filename,
                            {"data": {"dividends": {"rows": [{"exOrEffDate": f"{month}/{day}/{year}"}]}}})
        for symbol, filename in (("AAPL", "apple-ir-history.json"), ("AMZN", "amazon-ir-feed.json"),
                                 ("META", "meta-ir-history.json"), ("SPY", "spy-tickertech-proxy.json")):
            self.write_json("sources/postearn-supplement/" + filename,
                            {"GetStockQuoteHistoricalListResult": [{"HistoricalDate": day, "Last": float(price)}
                             for day, price in zip(("02/01/2024", "02/02/2024"), self.normalized["prices"][symbol]["close_cents"])]})
        apple = self.data / "sources/postearn-supplement/apple-dividend-page.html"
        apple.write_text("<p>生成夹具：最近已列示拆股2020年；不是发行人原件。</p>")
        self.write_workbook()
        for source in self.normalized["local_originals"]:
            self.refresh_hash(source["path"])
        self.save_normalized()

    def write_json(self, relative, value):
        path = self.data / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def refresh_hash(self, relative):
        body = (self.data / relative).read_bytes()
        source = next(s for s in self.normalized["local_originals"] if s["path"] == relative)
        source.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))

    def save_normalized(self):
        (self.folder / "normalized-evidence.json").write_text(json.dumps(self.normalized, ensure_ascii=False))

    def write_workbook(self):
        ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        sheet = ET.Element("{" + ns + "}worksheet")
        rows = ET.SubElement(sheet, "{" + ns + "}sheetData")
        for i, ex_date in enumerate(("12/15/2023", "03/15/2024"), 2):
            row = ET.SubElement(rows, "{" + ns + "}row", {"r": str(i)})
            for column, value in {"B": "SPY", "C": "78462F103", "D": ex_date}.items():
                cell = ET.SubElement(row, "{" + ns + "}c", {"r": column + str(i), "t": "inlineStr"})
                inline = ET.SubElement(cell, "{" + ns + "}is")
                ET.SubElement(inline, "{" + ns + "}t").text = value
        path = self.data / "sources/postearn-supplement/spy-ssga-distributions.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/worksheets/sheet1.xml", ET.tostring(sheet))
            archive.writestr("xl/workbook.xml", '<workbook xmlns="' + ns + '" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="dividend" sheetId="1" r:id="rId1"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')

    def calculate(self):
        auditor = AUDIT.Auditor.__new__(AUDIT.Auditor)
        auditor.data = self.data.resolve()
        auditor.sources = auditor.data / "sources"
        auditor.files = {}
        auditor.url_files = {}
        auditor.declared_missing = []
        auditor.used = set()
        return auditor.calculate(self.row, self.task, self.entity)

    def change_raw(self, relative, mutate):
        path = self.data / relative
        value = json.loads(path.read_text())
        mutate(value)
        self.write_json(relative, value)
        # 更新夹具完整性声明，确保负例由语义/计算核验拒绝，而非仅凭hash改变。
        self.refresh_hash(relative)
        self.save_normalized()

    def test_valid_finite_window_is_verified(self):
        result = self.calculate()
        self.assertTrue(all(result["checks"].values()), result["checks"])
        self.assertTrue(result["proof_complete"])
        self.assertEqual(result["computed_label"], "negative_reaction")

    def test_wrong_trading_date_is_rejected(self):
        self.change_raw("sources/earnings-credit/yahoo-AAPL-20240201-20240202.raw.json",
                        lambda v: v["chart"]["result"][0]["timestamp"].__setitem__(1, 1707143400))
        with self.assertRaises(KeyError):
            self.calculate()

    def test_wrong_price_is_rejected_after_hash_is_refreshed(self):
        self.change_raw("sources/earnings-credit/yahoo-AAPL-20240201-20240202.raw.json",
                        lambda v: v["chart"]["result"][0]["indicators"]["quote"][0]["close"].__setitem__(1, 200.0))
        result = self.calculate()
        self.assertFalse(result["checks"]["finite_window_original_evidence_reverified"])
        self.assertFalse(result["checks"]["reference_value_matches_original_source_calculation"])

    def test_window_ex_dividend_is_rejected_after_hash_is_refreshed(self):
        self.change_raw("sources/postearn-supplement/apple-nasdaq-dividend.json",
                        lambda v: v["data"]["dividends"]["rows"][0].update(exOrEffDate="02/02/2024"))
        result = self.calculate()
        self.assertFalse(result["checks"]["finite_window_original_evidence_reverified"])
        self.assertFalse(result["proof_complete"])

    def test_wrong_classification_threshold_is_rejected(self):
        self.entity["flat_threshold_abn_pct"] = 2
        result = self.calculate()
        self.assertFalse(result["checks"]["task_threshold_is_one_percentage_point"])
        self.assertFalse(result["checks"]["reference_label_matches_calculation"])

    def test_threshold_boundaries_are_flat(self):
        for value in (Fraction(1), Fraction(-1)):
            self.assertEqual(VERIFY.label(value), "flat")
        self.assertEqual(VERIFY.label(Fraction(1000001, 1000000)), "positive_reaction")
        self.assertEqual(VERIFY.label(Fraction(-1000001, 1000000)), "negative_reaction")

    def test_false_quality_status_is_rejected(self):
        self.row["quality"]["fact_status"] = "provisional"
        self.assertFalse(self.calculate()["checks"]["quality_fact_status_verified"])

    def test_saved_report_passed_cannot_replace_current_original_checks(self):
        self.write_json("sources/postearn-resolution/verification-originals.json", {"passed": True, "check_count": 157})
        self.change_raw("sources/postearn-supplement/meta-nasdaq-dividend.json",
                        lambda v: v["data"]["dividends"]["rows"][0].update(exOrEffDate="02/02/2024"))
        self.assertFalse(self.calculate()["checks"]["finite_window_original_evidence_reverified"])


if __name__ == "__main__":
    unittest.main()
