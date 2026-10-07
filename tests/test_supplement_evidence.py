"""补证清单的字节审计回归；不访问网络或修改真实研究资料。"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "tools/audit_reference_data.py"
SPEC = importlib.util.spec_from_file_location("audit_reference_data", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PRIVATE_CACHE = TOOL.parents[1] / ".local/private-evidence"


class SupplementEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name).resolve()
        self.folder = self.data / "sources/supplement"
        self.folder.mkdir(parents=True)
        self.body = b"public original response\n"
        (self.folder / "body.raw.txt").write_bytes(self.body)
        self.source = {"path": "body.raw.txt", "url": "https://example.test/source",
                       "sha256": hashlib.sha256(self.body).hexdigest(),
                       "bytes": len(self.body), "status": "downloaded"}

    def audit(self, sources):
        (self.folder / "evidence-manifest.json").write_text(json.dumps({
            "sources": sources, "checks": {"independent_formula": True},
            "limitations": ["研究结论另行复核"]}))
        auditor = MODULE.Auditor.__new__(MODULE.Auditor)
        auditor.data = self.data
        auditor.sources = self.data / "sources"
        auditor.files = {}
        auditor.url_files = {}
        auditor.declared_missing = []
        auditor.supplements = []
        auditor.supplement_errors = []
        auditor.index_supplement_evidence()
        return auditor

    def test_saved_body_hash_is_actually_read(self):
        auditor = self.audit([self.source])
        declaration = auditor.files["sources/supplement/body.raw.txt"]["declarations"][0]
        self.assertTrue(declaration["hash_match"])
        self.assertEqual(auditor.supplement_errors, [])
        self.assertEqual(auditor.supplements[0]["preserved_source_count"], 1)

    def test_changed_bytes_fail_hash_comparison(self):
        (self.folder / "body.raw.txt").write_bytes(b"changed original response\n")
        auditor = self.audit([self.source])
        self.assertFalse(auditor.files["sources/supplement/body.raw.txt"]["declarations"][0]["hash_match"])

    def test_downloaded_but_missing_body_is_an_error(self):
        (self.folder / "body.raw.txt").unlink()
        auditor = self.audit([self.source])
        self.assertEqual(len(auditor.supplement_errors), 1)
        self.assertEqual(auditor.supplements[0]["preserved_source_count"], 0)

    def test_parent_and_absolute_paths_are_rejected(self):
        for path in ("../outside.txt", str(self.folder / "body.raw.txt")):
            with self.subTest(path=path):
                auditor = self.audit([{**self.source, "path": path}])
                self.assertEqual(len(auditor.supplement_errors), 1)
                self.assertEqual(auditor.files, {})

    def test_symlink_escape_is_rejected(self):
        outside = self.data / "outside.txt"
        outside.write_bytes(self.body)
        (self.folder / "link.txt").symlink_to(outside)
        auditor = self.audit([{**self.source, "path": "link.txt"}])
        self.assertEqual(len(auditor.supplement_errors), 1)
        self.assertEqual(auditor.files, {})

    def test_wrong_declared_length_is_an_error(self):
        auditor = self.audit([{**self.source, "bytes": len(self.body) + 1}])
        self.assertEqual(len(auditor.supplement_errors), 1)

    def test_unavailable_sources_do_not_count_as_saved_evidence(self):
        auditor = self.audit([{**self.source, "status": "unavailable"}])
        self.assertEqual(auditor.files, {})
        self.assertEqual(auditor.supplements[0]["preserved_source_count"], 0)

    def test_invalid_hash_is_not_accepted(self):
        auditor = self.audit([{**self.source, "sha256": "unknown"}])
        self.assertEqual(len(auditor.supplement_errors), 1)
        self.assertEqual(auditor.files, {})

    def test_directory_cannot_be_a_source_body(self):
        (self.folder / "directory").mkdir()
        auditor = self.audit([{**self.source, "path": "directory"}])
        self.assertEqual(len(auditor.supplement_errors), 1)
        self.assertEqual(auditor.files, {})

    def test_non_object_source_is_an_error(self):
        auditor = self.audit(["body.raw.txt"])
        self.assertEqual(len(auditor.supplement_errors), 1)

    def test_research_results_keep_their_explicit_scope(self):
        auditor = self.audit([self.source])
        self.assertEqual(auditor.supplements[0]["research_checks"], {"independent_formula": True})
        self.assertIn("不计作本工具独立公式复算", auditor.supplements[0]["scope"])


class OriginalEventBodyTests(unittest.TestCase):
    def test_html_entities_and_hidden_script_are_handled(self):
        result = MODULE.visible_html_text('<script>On April 1, 2020</script><p>Chapter&#160;<b>11</b></p>')
        self.assertEqual(result, "Chapter 11")

    def test_completed_petition_date_is_parsed(self):
        text = 'On November 6, 2023 (the “Petition Date”), WeWork Inc. and its subsidiaries filed voluntary petitions to commence proceedings under Chapter 11.'
        self.assertEqual(MODULE.chapter11_notice_date(text, r"WeWork Inc\."), "2023-11-06")

    def test_different_company_cannot_supply_the_event(self):
        text = 'On August 6, 2023, Yellow Corporation filed a voluntary petition under Chapter 11.'
        with self.assertRaises(ValueError):
            MODULE.chapter11_notice_date(text, r"Rite Aid Corporation")

    def test_planned_petition_is_not_a_completed_event(self):
        text = 'On August 6, 2023, Yellow Corporation plans to file a voluntary petition under Chapter 11.'
        with self.assertRaises(ValueError):
            MODULE.chapter11_notice_date(text, r"Yellow Corporation")

    def test_candidate_negative_label_cannot_skip_saved_positive_body(self):
        with tempfile.TemporaryDirectory() as directory:
            auditor = MODULE.Auditor.__new__(MODULE.Auditor)
            auditor.data = Path(directory).resolve()
            auditor.sources = auditor.data / "sources"
            auditor.files = {}; auditor.url_files = {}; auditor.used = set()
            folder = auditor.sources / "credit-supplement/documents/BBBY"
            folder.mkdir(parents=True)
            (folder / "event8k.htm").write_text('<p>On April 23, 2023, Bed Bath and Beyond, Inc. filed a voluntary petition under Chapter 11.</p>')
            result = auditor.calculate({"task_id": "t4-credit-event-2023", "entity_id": "BBBY",
                "reference_label": "no_event", "status": "provisional", "reference_value": None,
                "inputs": [{"name": "chapter_11_filing_date", "value": "2023-04-23"}]},
                {"cutoff_date": "2023-03-31", "resolution_date": "2024-03-31"}, {})
            self.assertEqual(result["computed_label"], "credit_event")
            self.assertFalse(result["checks"]["reference_label_matches_original_event"])


class EarningsSourceDateTests(unittest.TestCase):
    def test_webcast_notice_is_separate_from_actual_release(self):
        sources = [
            {"title": "AMGEN ANNOUNCES WEBCAST OF 2023 SECOND QUARTER FINANCIAL RESULTS",
             "url": "https://www.amgen.com/newsroom/press-releases/2023/07/amgen-announces-webcast-of-2023-second-quarter-financial-results",
             "published_at": "2023-07-31"},
            {"title": "AMGEN REPORTS SECOND QUARTER FINANCIAL RESULTS",
             "url": "https://www.amgen.com/newsroom/press-releases/2023/08/amgen-reports-second-quarter-financial-results",
             "published_at": "2023-08-03"},
            {"title": "Amgen reports second quarter financial results",
             "url": "https://example.test/duplicate-release", "published_at": "2023-08-03"},
            {"title": "Amgen reports first quarter financial results",
             "url": "https://example.test/earlier-release", "published_at": "2023-04-27"},
            {"title": "AMGEN REPORTS SECOND QUARTER FINANCIAL RESULTS",
             "url": "https://example.test/amgen-announces-webcast-of-financial-results",
             "published_at": "2023-07-31"},
        ]
        dates = MODULE.earnings_source_dates(sources)
        self.assertEqual(dates["declared_release_dates"], ["2023-04-27", "2023-08-03"])
        self.assertEqual(dates["declared_schedule_notice_dates"], ["2023-07-31"])
        self.assertEqual(dates["declared_filing_dates"], [])
        self.assertEqual(dates["declared_presentation_dates"], [])
        self.assertEqual(dates["declared_other_source_dates"], [])

    def test_form_10q_is_filing_even_when_title_mentions_results(self):
        dates = MODULE.earnings_source_dates([
            {"title": "Amgen Form 10-Q: reports second quarter financial results",
             "url": "https://www.sec.gov/Archives/edgar/data/318154/quarterly-report.htm",
             "published_at": "2023-08-04"},
            {"title": "Amgen Form 10-K", "url": "https://example.test/annual-report.htm",
             "published_at": "2024-02-14"},
        ])
        self.assertEqual(dates["declared_filing_dates"], ["2023-08-04", "2024-02-14"])
        self.assertEqual(dates["declared_release_dates"], [])
        self.assertEqual(dates["declared_schedule_notice_dates"], [])

    def test_earnings_presentation_has_its_own_date_role(self):
        dates = MODULE.earnings_source_dates([
            {"title": "Earnings Presentation: Amgen reports second quarter financial results",
             "url": "https://example.test/earnings-presentation.pdf",
             "published_at": "2023-08-03"},
        ])
        self.assertEqual(dates["declared_presentation_dates"], ["2023-08-03"])
        self.assertEqual(dates["declared_release_dates"], [])
        self.assertEqual(dates["declared_filing_dates"], [])

    def test_unknown_or_undated_sources_cannot_supply_release_date(self):
        dates = MODULE.earnings_source_dates([
            {"title": "SEC Company Concept: Amgen EarningsPerShareDiluted",
             "url": "https://data.sec.gov/api/xbrl/companyconcept/CIK0000318154/us-gaap/EarningsPerShareDiluted.json",
             "published_at": "2023-08-04"},
            {"title": "Amgen reports financial results", "url": "https://example.test/no-date"},
            {"title": "Amgen reports financial results", "url": "https://example.test/null-date",
             "published_at": None},
            {"title": "Amgen reports financial results", "url": "https://example.test/empty-date",
             "published_at": ""},
        ])
        self.assertEqual(dates["declared_other_source_dates"], ["2023-08-04"])
        self.assertEqual(dates["declared_release_dates"], [])
        self.assertEqual(dates["declared_schedule_notice_dates"], [])
        self.assertEqual(dates["declared_filing_dates"], [])
        self.assertEqual(dates["declared_presentation_dates"], [])

    def test_amgn_original_dateline_rejects_wrong_company_or_date_role(self):
        actual = ("THOUSAND OAKS, Calif. , Aug. 3, 2023 /PRNewswire/ -- Amgen (NASDAQ:AMGN) "
                  "today announced financial results for the second quarter of 2023.")
        notice = ("THOUSAND OAKS, Calif. , July 31, 2023 /PRNewswire/ -- Amgen (NASDAQ:AMGN) "
                  "today announced that it will report its second quarter financial results on August 3, 2023.")
        self.assertEqual(MODULE.amgn_original_dateline(actual), "2023-08-03")
        self.assertEqual(MODULE.amgn_original_dateline(notice, schedule_notice=True), "2023-07-31")
        for text in (notice, actual.replace("NASDAQ:AMGN", "NASDAQ:OTHER"),
                     actual.replace("second quarter of 2023", "first quarter of 2023")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                MODULE.amgn_original_dateline(text)
        with self.assertRaises(ValueError):
            MODULE.amgn_original_dateline(actual, schedule_notice=True)

    @unittest.skipUnless(PRIVATE_CACHE.is_dir(), "实际SEC/IR原件需本地隔离证据缓存；公开套件不伪造原件")
    def test_saved_amgn_clarification_keeps_actual_date_and_allows_aligned_verified(self):
        from tools.public_sources import materialized_dataset
        data = TOOL.parents[1] / "datasets/agenthon-t4-reference"
        task_id = "t4-eps-yoy-2023Q2-mixed"
        rows = [json.loads(line) for line in (data / "reference.jsonl").read_text().splitlines()]
        row = next(row for row in rows if row["task_id"] == task_id and row["entity_id"] == "AMGN")
        task = json.loads((data / "inputs/units" / task_id / "task.json").read_text())
        entity = next(entity for entity in task["entities"] if entity["entity_id"] == "AMGN")
        overrides = json.loads((data / "research/resolution-overrides.json").read_text())["records"]
        override = next(item for item in overrides if item["task_id"] == task_id and item["entity_id"] == "AMGN")
        with materialized_dataset(data, PRIVATE_CACHE) as effective:
            auditor = MODULE.Auditor(effective)
            for status in ("verified", "provisional"):
                candidate = copy.deepcopy(row)
                candidate["status"] = status
                candidate["quality"] = copy.deepcopy(override["quality"])
                result = auditor.calculate(candidate, task, entity)
                self.assertEqual(result["computed_value"], 2.57)
                self.assertEqual(result["computed_label"], "up")
                self.assertEqual(result["date_semantics"]["declared_release_dates"], ["2023-08-03"])
                self.assertEqual(result["date_semantics"]["declared_schedule_notice_dates"], ["2023-07-31"])
                self.assertEqual(result["date_semantics"]["release_vs_resolution"], "release_after_resolution")
                self.assertNotIn("late_release_kept_provisional", result["checks"])
                self.assertTrue(all(result["checks"].values()))
                self.assertEqual(result["date_semantics"]["resolution_date_role"], "context_only")
                self.assertEqual(result["date_semantics"]["expected_report_date"], "2023-08-01")
                self.assertEqual(result["date_semantics"]["original_actual_release_date"], "2023-08-03")
                self.assertFalse(result["proof_complete"])
            # 将预告日期冒用为实际公告日期，必须由保存原件抓住；不再把合法升级当错误。
            candidate = copy.deepcopy(row)
            candidate["status"] = "verified"
            candidate["quality"] = copy.deepcopy(override["quality"])
            for source in candidate["sources"]:
                if "/2023/08/amgen-reports-second-quarter-financial-results" in source["url"]:
                    source["published_at"] = "2023-07-31"
            result = auditor.calculate(candidate, task, entity)
            self.assertFalse(result["checks"]["actual_release_date_matches_original_dateline"])
            self.assertEqual(result["date_semantics"]["original_actual_release_date"], "2023-08-03")
            self.assertTrue(result["checks"]["schedule_notice_date_matches_original_dateline"])
            self.assertEqual(result["date_semantics"]["release_vs_resolution"], "release_after_resolution")
            self.assertEqual(result["date_semantics"]["declared_release_vs_resolution"], "release_on_or_before_resolution")

    def test_amgn_clarification_does_not_remove_other_eps_date_guards(self):
        auditor = MODULE.Auditor.__new__(MODULE.Auditor)
        observations = [{"start": "2023-04-01", "end": "2023-06-30", "val": 3.0,
                         "form": "10-Q", "filed": "2023-08-04", "accn": "synthetic"},
                        {"start": "2022-04-01", "end": "2022-06-30", "val": 2.0,
                         "form": "10-Q", "filed": "2022-08-04", "accn": "synthetic-prior"}]
        auditor.eps_observations = lambda symbol: (observations, {}, "明确合成测试")
        task = {"cutoff_date": "2023-07-14", "resolution_date": "2023-08-02"}
        entity = {"quarter_reported": "2023-06-30", "prior_year_quarter": "2022-06-30", "prior_year_q_eps": 2.0}
        row = {"task_id": "t4-eps-yoy-2023Q2-mixed", "entity_id": "SYNTHETIC",
               "target_type": "classification", "reference_value": 3.0, "reference_label": "up", "sources": [
            {"title": "Synthetic reports second quarter results", "url": "https://example.test/release",
             "published_at": "2023-08-03"}]}
        for status, accepted in (("verified", False), ("provisional", True)):
            row["status"] = status
            result = auditor.calculate(row, task, entity)
            self.assertIs(result["checks"]["late_release_kept_provisional"], accepted)


if __name__ == "__main__":
    unittest.main()
