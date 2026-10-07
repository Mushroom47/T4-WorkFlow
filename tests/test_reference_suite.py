"""标准库端到端错误场景：冻结身份、roster、引用和本地描述性指标。"""
import contextlib
import copy
import hashlib
import io
import json
import math
import pathlib
import shutil
import tempfile
import unittest

from tools.reference_suite import (DEFAULT_ROOT, ReferenceSuite, SuiteError, canonical_hash,
                                   main, parse_json, spearman, task_table)


# 无外部服务和第三方依赖；已冻结真实 schema 时优先用该版本。
FALLBACK_SCHEMA = {
    "type": "object", "required": ["task_id", "entity_predictions"],
    "properties": {
        "task_id": {"type": "string"},
        "target_type": {"enum": ["classification", "regression", "ranking"]},
        "entity_predictions": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["entity_id", "interval", "claims"],
            "properties": {
                "entity_id": {"type": "string"}, "label": {"type": "string"},
                "point_forecast": {"type": "number"}, "rank": {"type": "integer"},
                "interval": {"type": "object", "required": ["level", "lo", "hi"],
                             "properties": {"level": {"type": "number", "const": 0.9},
                                            "lo": {"type": "number"}, "hi": {"type": "number"}}},
                "claims": {"type": "array", "minItems": 1, "items": {
                    "type": "object", "required": ["doc_id", "span_start", "span_end", "claim"],
                    "properties": {"doc_id": {"type": "string"}, "span_start": {"type": "integer", "minimum": 0},
                                   "span_end": {"type": "integer", "minimum": 0}, "claim": {"type": "string"}}}},
            }, "allOf": [{"if": {"properties": {"rank": {"type": "integer"}}, "required": ["rank"]},
                          "then": {"required": ["point_forecast"]}}]}},
        "submitted_reasons": {"type": "array", "minItems": 1, "maxItems": 3, "items": {
            "type": "object", "required": ["reason_id", "premise", "mechanism", "answer_implication"],
            "properties": {"reason_id": {"type": "string"}, "premise": {"type": "string"},
                           "mechanism": {"type": "string"}, "answer_implication": {"type": "string"},
                           "scope": {"type": "object", "properties": {"entities": {"type": "array", "items": {"type": "string"}}}},
                           "citations": {"type": "array", "items": {"type": "object", "required": ["doc_id", "span_start", "span_end"],
                              "properties": {"doc_id": {"type": "string"}, "span_start": {"type": "integer", "minimum": 0},
                                             "span_end": {"type": "integer", "minimum": 0}}}}}}},
    },
}


class ReferenceSuiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.task_id = "t4-local-test"
        self.unit = self.root / "inputs/units" / self.task_id
        self.unit.mkdir(parents=True)
        self.task = {"task_id": self.task_id, "schema_version": "3",
                     "target": {"type": "classification", "labels": ["up", "down"]},
                     "cutoff_date": "2024-01-01", "resolution_date": "2024-02-01", "interval_level": 0.9,
                     "entities": [{"entity_id": "A", "name": "甲公司", "prior": 5.0},
                                  {"entity_id": "B", "name": "乙公司", "prior": 6.0}]}
        self.documents = {
            "A_history": {"doc_id": "A_history", "doc_date": "2023-12-15",
                          "text": "甲公司 Revenue was 100 units. This historical report supplies input context."},
            "B_history": {"doc_id": "B_history", "doc_date": "2023-12-15",
                          "text": "乙公司 Revenue was 200 units. This historical report supplies input context."},
        }
        self.refs = [{"task_id": self.task_id, "entity_id": eid, "target_type": "classification",
                      "reference_label": label, "reference_value": value, "unit": "USD/share", "status": "verified",
                      "method": "独立合成数据用于测试，不对应真实事件。", "inputs": [],
                      "quality": {"fact_status": "verified", "task_alignment": "aligned",
                                  "first_publication_status": "unconfirmed", "official_outcome_status": "unconfirmed",
                                  "acceptance_scope": "独立合成数据用于测试。"},
                      "sources": [{"url": "https://example.org/evidence", "title": "测试证据", "published_at": None,
                                   "locator": "用于离线测试的合成记录。"}], "notes": []}
                     for eid, label, value in (("A", "up", 1.0), ("B", "down", 2.0))]
        actual = DEFAULT_ROOT / "inputs/schemas/analysis.schema.json"
        self.schema = json.loads(actual.read_text()) if actual.is_file() else copy.deepcopy(FALLBACK_SCHEMA)
        self.build_bundle()

    def dump(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def build_bundle(self, kind=None):
        if kind:
            self.task["target"]["type"] = kind
            for row in self.refs:
                row["target_type"] = kind
                if kind != "classification":
                    row["reference_label"] = None
        self.dump(self.unit / "task.json", self.task)
        files = []
        for doc_id, document in self.documents.items():
            path = self.unit / "corpus" / (doc_id + ".json")
            self.dump(path, document)
            files.append({"path": "corpus/" + path.name, "role": "corpus",
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "entity_ids": [doc_id[0]]})
        self.dump(self.unit / "manifest.json", {"files": files})
        schema_path = self.root / "inputs/schemas/analysis.schema.json"
        self.dump(schema_path, self.schema)
        source = {"schema_version": "0.1.0", "units": [{"task_id": self.task_id,
                  "task_path": f"units/{self.task_id}/task.json",
                  "task_sha256": hashlib.sha256((self.unit / "task.json").read_bytes()).hexdigest(),
                  "task_canonical_sha256": canonical_hash(self.task),
                  "files": [{"path": str(p.relative_to(self.root / "inputs")),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in self.unit.rglob("*") if p.is_file()]}],
                  "schemas": [{"path": "schemas/analysis.schema.json",
                               "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest()}]}
        self.dump(self.root / "inputs/source-manifest.json", source)
        for row in self.refs:
            row["task_canonical_sha256"] = canonical_hash(self.task)
        self.write_refs()
        self.suite = ReferenceSuite(self.root)

    def write_refs(self):
        (self.root / "reference.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.refs))

    def answer(self):
        return self.suite.fixture(self.task_id)

    def test_audit_exact_roster_and_reference_keys(self):
        result = self.suite.audit(expected_records=2, expected_tasks=1)
        self.assertEqual(result["records"], 2)
        self.assertEqual(result["status_counts"], {"verified": 2})

    def test_verified_cannot_hide_task_alignment_conflict(self):
        self.refs[0]["quality"] = {"fact_status": "verified", "task_alignment": "ambiguous",
            "first_publication_status": "unconfirmed", "official_outcome_status": "unconfirmed",
            "acceptance_scope": "事实确认，但题面日期未澄清。"}
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "task 对齐歧义"):
            ReferenceSuite(self.root)

    def test_unsupported_official_confirmation_is_refused(self):
        self.refs[0]["quality"] = {"fact_status": "verified", "task_alignment": "aligned",
            "first_publication_status": "unconfirmed", "official_outcome_status": "confirmed",
            "acceptance_scope": "合成测试。"}
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "official_evidence"):
            ReferenceSuite(self.root)

    def test_new_reference_schema_requires_quality_on_every_row(self):
        del self.refs[0]["quality"]
        self.write_refs()
        self.dump(self.root / "build-report.json", {"schema_version": "0.2.0"})
        with self.assertRaisesRegex(SuiteError, "缺少 quality"):
            ReferenceSuite(self.root)

    def test_missing_quality_cannot_be_bypassed_by_removing_build_report(self):
        del self.refs[0]["quality"]
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "缺少 quality"):
            ReferenceSuite(self.root)

    def test_arbitrary_official_evidence_cannot_claim_confirmation(self):
        for fabricated in ("任意字符串", {"score": 100, "submission_id": "fake"}):
            self.refs[0]["quality"].update(official_outcome_status="confirmed", official_evidence=fabricated)
            self.write_refs()
            with self.assertRaisesRegex(SuiteError, "不能声明 confirmed"):
                ReferenceSuite(self.root)

    def test_bounded_fact_scope_is_visible_in_comparison(self):
        self.refs[0]["quality"] = {"fact_status": "bounded_verified", "task_alignment": "aligned",
            "first_publication_status": "not_applicable", "official_outcome_status": "unconfirmed",
            "acceptance_scope": "仅限定主体与窗口的公开证据验收。"}
        self.write_refs()
        self.suite = ReferenceSuite(self.root)
        result = self.suite.compare(self.answer())["entities"][0]
        self.assertEqual(result["quality"]["fact_status"], "bounded_verified")
        self.assertEqual(result["inclusion_basis"], "local_verified")

    def test_audit_checks_frozen_license_hashes(self):
        path = self.root / "inputs/LICENSE"
        path.write_text("离线测试许可证文本。", encoding="utf-8")
        manifest_path = self.root / "inputs/source-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["license_files"] = [{"path": "LICENSE", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]
        self.dump(manifest_path, manifest)
        self.assertTrue(ReferenceSuite(self.root).audit(2, 1)["ok"])
        path.write_text("文件已变化。", encoding="utf-8")
        with self.assertRaisesRegex(SuiteError, "SHA-256"):
            ReferenceSuite(self.root).audit(2, 1)

    def test_audit_rejects_inconsistent_manifest_counts(self):
        path = self.root / "inputs/source-manifest.json"
        manifest = json.loads(path.read_text())
        manifest["entity_count"] = 3
        self.dump(path, manifest)
        with self.assertRaisesRegex(SuiteError, "task_count/entity_count"):
            ReferenceSuite(self.root).audit(2, 1)

    def test_unknown_task_is_refused_without_fuzzy_lookup(self):
        with self.assertRaisesRegex(SuiteError, "未知 task_id"):
            self.suite.fixture("t4-local-tes")

    def test_task_semantic_change_is_refused(self):
        changed = copy.deepcopy(self.task)
        changed["entities"][0]["prior"] = 999
        with self.assertRaisesRegex(SuiteError, "canonical SHA-256"):
            self.suite.fixture(self.task_id, supplied_task=changed)

    def test_external_task_whitespace_and_key_order_do_not_change_identity(self):
        reformatted = json.loads(json.dumps(self.task, sort_keys=True, ensure_ascii=True))
        answer = self.suite.fixture(self.task_id, supplied_task=reformatted)
        self.assertTrue(self.suite.validate(answer, reformatted)["ok"])

    def test_supplied_task_key_order_drives_spans_without_mutating_frozen_cache(self):
        frozen = self.suite.load_unit(self.task_id)
        text_before, ranges_before = frozen["text"], copy.deepcopy(frozen["ranges"])
        supplied = json.loads(json.dumps(self.task, sort_keys=True, ensure_ascii=True))
        text, ranges = task_table(supplied)
        answer = self.suite.fixture(self.task_id, supplied_task=supplied)
        for row in answer["entity_predictions"]:
            cite = row["claims"][0]
            start, end = cite["span_start"], cite["span_end"]
            self.assertEqual(text[start:end], '"prior": ' + str(supplied["entities"][0 if row["entity_id"] == "A" else 1]["prior"]))
            lo, hi = ranges[row["entity_id"]]
            self.assertTrue(lo <= start < end <= hi)
        view = self.suite.load_unit(self.task_id, supplied)
        self.assertIsNot(view, frozen)
        self.assertEqual(self.suite.load_unit(self.task_id)["text"], text_before)
        self.assertEqual(self.suite.load_unit(self.task_id)["ranges"], ranges_before)
        frozen_answer = self.answer()
        cite = frozen_answer["entity_predictions"][0]["claims"][0]
        self.assertEqual(text_before[cite["span_start"]:cite["span_end"]], '"prior": 5.0')

    @unittest.skipUnless((DEFAULT_ROOT / "inputs/units/t4-fomc-curve-20220728/task.json").is_file(),
                         "本地冻结公开输入不存在")
    def test_real_fomc_supplied_task_reordered_claim_matches_actual_input(self):
        suite = ReferenceSuite(DEFAULT_ROOT)
        tid = "t4-fomc-curve-20220728"
        frozen = suite.load_unit(tid)
        supplied = json.loads(json.dumps(frozen["task"], sort_keys=True))
        actual_text, actual_ranges = task_table(supplied)
        answer = suite.fixture(tid, supplied_task=supplied)
        for entity, row in zip(supplied["entities"], answer["entity_predictions"]):
            cite = row["claims"][0]
            selected = next((k, v) for k, v in entity.items() if isinstance(v, (int, float))
                            and not isinstance(v, bool) and k != "entity_id")
            fragment = json.dumps(selected[0]) + ": " + json.dumps(selected[1])
            self.assertEqual(actual_text[cite["span_start"]:cite["span_end"]], fragment)
            lo, hi = actual_ranges[row["entity_id"]]
            self.assertTrue(lo <= cite["span_start"] < cite["span_end"] <= hi)
        self.assertTrue(suite.validate(answer, supplied)["ok"])
        self.assertEqual(suite.load_unit(tid)["text"], task_table(frozen["task"])[0])

    def test_frozen_input_mutation_is_refused(self):
        path = self.unit / "corpus/A_history.json"
        path.write_text(path.read_text() + " ")
        with self.assertRaisesRegex(SuiteError, "SHA-256"):
            self.suite.fixture(self.task_id)

    def test_reference_duplicate_key_is_refused(self):
        self.refs.append(copy.deepcopy(self.refs[0]))
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "重复实体键"):
            ReferenceSuite(self.root)

    def test_reference_task_hash_must_match_for_audit_fixture_and_compare(self):
        answer = self.answer()
        self.refs[0]["task_canonical_sha256"] = "0" * 64
        self.write_refs()
        suite = ReferenceSuite(self.root)
        actions = (lambda: suite.audit(2, 1), lambda: suite.fixture(self.task_id),
                   lambda: suite.compare(answer))
        for action in actions:
            with self.subTest(action=action), self.assertRaisesRegex(SuiteError, "参考项 task canonical SHA-256"):
                action()

    def test_reference_missing_or_invalid_task_hash_is_refused(self):
        original = copy.deepcopy(self.refs[0])
        for mode in ("missing", "invalid"):
            self.refs[0] = copy.deepcopy(original)
            if mode == "missing":
                del self.refs[0]["task_canonical_sha256"]
            else:
                self.refs[0]["task_canonical_sha256"] = "invalid"
            self.write_refs()
            with self.subTest(mode=mode), self.assertRaises(SuiteError):
                ReferenceSuite(self.root)

    def test_missing_reference_record_is_not_silently_dropped(self):
        self.refs.pop()
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "缺少实体"):
            ReferenceSuite(self.root).audit(2, 1)

    def test_missing_duplicate_or_unknown_answer_entity_is_refused(self):
        original = self.answer()
        for mode in ("missing", "duplicate", "unknown"):
            with self.subTest(mode=mode):
                answer = copy.deepcopy(original)
                if mode == "missing":
                    answer["entity_predictions"].pop()
                elif mode == "duplicate":
                    answer["entity_predictions"][1] = copy.deepcopy(answer["entity_predictions"][0])
                else:
                    answer["entity_predictions"][1]["entity_id"] = "UNKNOWN"
                with self.assertRaises(SuiteError):
                    self.suite.validate(answer)

    def test_illegal_label_is_refused(self):
        answer = self.answer()
        answer["entity_predictions"][0]["label"] = "flat"
        with self.assertRaisesRegex(SuiteError, "非法分类 label"):
            self.suite.validate(answer)

    def test_nan_in_memory_and_json_are_refused(self):
        answer = self.answer()
        answer["entity_predictions"][0]["point_forecast"] = math.nan
        with self.assertRaises(SuiteError):
            self.suite.validate(answer)
        with self.assertRaisesRegex(SuiteError, "非有限"):
            parse_json('{"value": NaN}')

    def test_null_or_boolean_point_is_not_a_number(self):
        original = self.answer()
        for value in (None, True, "1"):
            with self.subTest(value=value):
                answer = copy.deepcopy(original)
                answer["entity_predictions"][0]["point_forecast"] = value
                with self.assertRaises(SuiteError):
                    self.suite.validate(answer)

    def test_interval_level_order_missing_bound_and_overflow_are_refused(self):
        original = self.answer()
        changes = ({"level": 0.95}, {"lo": 3, "hi": 2}, {"lo": -1e308, "hi": 1e308})
        for change in changes:
            with self.subTest(change=change):
                answer = copy.deepcopy(original)
                answer["entity_predictions"][0]["interval"].update(change)
                with self.assertRaises(SuiteError):
                    self.suite.validate(answer)
        del original["entity_predictions"][0]["interval"]["hi"]
        with self.assertRaises(SuiteError):
            self.suite.validate(original)

    def test_point_outside_interval_is_not_an_official_schema_rule(self):
        answer = self.answer()
        answer["entity_predictions"][0]["point_forecast"] = 999.0
        self.assertTrue(self.suite.validate(answer)["ok"])

    def test_unicode_offsets_are_characters_not_bytes(self):
        answer = self.answer()
        text, ranges = task_table(self.task)
        cite = answer["entity_predictions"][0]["claims"][0]
        self.assertEqual(text[cite["span_start"]:cite["span_end"]], '"prior": 5.0')
        self.assertGreater(len(text[:cite["span_start"]].encode("utf-8")), cite["span_start"])
        cite["span_start"] = len(text[:cite["span_start"]].encode("utf-8"))
        cite["span_end"] = ranges["A"][1] + 1
        with self.assertRaisesRegex(SuiteError, "自己的行"):
            self.suite.validate(answer)

    def test_whole_number_float_spans_match_official_integer_semantics(self):
        answer = self.answer()
        claim = answer["entity_predictions"][0]["claims"][0]
        reason = answer["submitted_reasons"][0]["citations"][0]
        for cite in (claim, reason):
            cite["span_start"], cite["span_end"] = float(cite["span_start"]), float(cite["span_end"])
        self.assertTrue(self.suite.validate(answer)["ok"])

    def test_fractional_boolean_nonfinite_and_negative_spans_are_refused(self):
        original = self.answer()
        for value in (0.5, True, math.nan, math.inf, -1.0):
            answer = copy.deepcopy(original)
            answer["entity_predictions"][0]["claims"][0]["span_start"] = value
            with self.subTest(value=value), self.assertRaises(SuiteError):
                self.suite.validate(answer)

    def test_task_span_cannot_cross_rows_or_cite_another_entity(self):
        original = self.answer()
        _, ranges = task_table(self.task)
        for bounds in ((ranges["A"][0], ranges["B"][1]), ranges["B"]):
            with self.subTest(bounds=bounds):
                answer = copy.deepcopy(original)
                cite = answer["entity_predictions"][0]["claims"][0]
                cite["span_start"], cite["span_end"] = bounds
                with self.assertRaisesRegex(SuiteError, "自己的行"):
                    self.suite.validate(answer)

    def test_empty_outside_and_overlong_corpus_spans_are_refused(self):
        original = self.answer()
        for start, end in ((0, 0), (-1, 4), (0, 9000)):
            with self.subTest(start=start, end=end):
                answer = copy.deepcopy(original)
                answer["entity_predictions"][0]["claims"] = [{"doc_id": "A_history", "span_start": start,
                                                             "span_end": end, "claim": "历史营收为 100。"}]
                with self.assertRaises(SuiteError):
                    self.suite.validate(answer)

    def test_corpus_document_must_belong_to_claim_entity(self):
        answer = self.answer()
        answer["entity_predictions"][0]["claims"] = [{"doc_id": "B_history", "span_start": 0,
                                                     "span_end": 10, "claim": "历史输入。"}]
        with self.assertRaisesRegex(SuiteError, "不属于该实体"):
            self.suite.validate(answer)

    def test_post_cutoff_document_is_refused_even_when_manifest_hashes_match(self):
        self.documents["B_history"]["doc_date"] = "2024-01-02"
        self.build_bundle()
        answer = self.answer()
        answer["entity_predictions"][1]["claims"] = [{"doc_id": "B_history", "span_start": 0,
                                                     "span_end": 10, "claim": "历史输入。"}]
        with self.assertRaisesRegex(SuiteError, "晚于 cutoff"):
            self.suite.validate(answer)

    def test_reasons_require_fields_and_one_to_three_entries(self):
        original = self.answer()
        for mode in ("missing_field", "empty", "too_many"):
            with self.subTest(mode=mode):
                answer = copy.deepcopy(original)
                if mode == "missing_field":
                    del answer["submitted_reasons"][0]["mechanism"]
                elif mode == "empty":
                    answer["submitted_reasons"] = []
                else:
                    answer["submitted_reasons"] *= 4
                with self.assertRaises(SuiteError):
                    self.suite.validate(answer)

    def test_reasons_cannot_cite_task_or_unknown_scope_entity(self):
        original = self.answer()
        answer = copy.deepcopy(original)
        answer["submitted_reasons"][0]["citations"] = [answer["entity_predictions"][0]["claims"][0]]
        with self.assertRaisesRegex(SuiteError, "不能引用 task"):
            self.suite.validate(answer)
        original["submitted_reasons"][0]["scope"]["entities"] = ["UNKNOWN"]
        with self.assertRaisesRegex(SuiteError, "未知实体"):
            self.suite.validate(original)

    def test_fixture_is_honest_about_synthetic_interval_and_unchecked_nli(self):
        answer = self.answer()
        self.assertTrue(answer["notes"]["synthetic_interval"])
        self.assertEqual(answer["notes"]["faithfulness"], "not_evaluated")
        self.assertEqual(answer["entity_predictions"][0]["point_forecast"], 1.0)
        self.assertIn("5.0", answer["entity_predictions"][0]["claims"][0]["claim"])
        self.assertNotIn("1.0", answer["entity_predictions"][0]["claims"][0]["claim"])

    def test_provisional_needs_explicit_fixture_flag_and_unresolved_always_refused(self):
        self.refs[0]["status"] = "provisional"
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "provisional"):
            self.answer()
        self.suite.fixture(self.task_id, allow_provisional=True)
        self.refs[0]["status"] = "unresolved"
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "unresolved"):
            self.suite.fixture(self.task_id, allow_provisional=True)

    def test_compare_metrics_have_known_values_and_no_composite(self):
        answer = self.answer()
        a, b = answer["entity_predictions"]
        a.update({"label": "down", "point_forecast": 2.5,
                  "interval": {"level": 0.9, "lo": 1.5, "hi": 2.0}})
        b["interval"] = {"level": 0.9, "lo": 1.0, "hi": 3.0}
        report = self.suite.compare(answer)
        self.assertEqual(report["classification_accuracy"], 0.5)
        self.assertEqual(report["mean_absolute_error"], 0.75)
        self.assertEqual(report["interval_coverage"], 0.5)
        self.assertEqual(report["mean_interval_score_90"], 6.25)
        self.assertNotIn("composite", report)

    def test_compare_excludes_provisional_and_unresolved_explicitly(self):
        answer = self.answer()
        self.refs[0]["status"] = "provisional"
        self.refs[1]["status"] = "unresolved"
        self.build_bundle()
        report = self.suite.compare(answer)
        self.assertEqual(report["included_count"], 0)
        self.assertIsNone(report["mean_absolute_error"])
        self.assertEqual(report["reference_status_counts"], {"provisional": 1, "unresolved": 1})
        report = self.suite.compare(answer, allow_provisional=True)
        self.assertEqual(report["included_count"], 1)

    def test_compare_refuses_verified_classification_without_primary_label(self):
        answer = self.answer()
        self.refs[0]["reference_label"] = None
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "分类参考缺少 reference_label"):
            self.suite.compare(answer)
        with self.assertRaisesRegex(SuiteError, "分类参考缺少 reference_label"):
            self.answer()

    def test_compare_refuses_verified_regression_without_primary_value(self):
        self.build_bundle("regression")
        answer = self.answer()
        self.refs[0]["reference_value"] = None
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "数值参考缺少 reference_value"):
            self.suite.compare(answer)
        with self.assertRaisesRegex(SuiteError, "数值参考缺少 reference_value"):
            self.answer()

    def test_provisional_missing_primary_is_refused_when_explicitly_included(self):
        answer = self.answer()
        self.refs[0]["status"] = "provisional"
        self.refs[0]["reference_label"] = None
        self.build_bundle()
        self.assertEqual(self.suite.compare(answer)["included_count"], 1)
        with self.assertRaisesRegex(SuiteError, "分类参考缺少 reference_label"):
            self.suite.compare(answer, allow_provisional=True)
        with self.assertRaisesRegex(SuiteError, "分类参考缺少 reference_label"):
            self.suite.fixture(self.task_id, allow_provisional=True)

    def test_pure_label_fixture_does_not_invent_probability_truth(self):
        for row in self.refs:
            row["reference_value"] = None
        self.build_bundle()
        answer = self.answer()
        self.assertEqual(answer["entity_predictions"][0]["point_forecast"], 0.5)
        self.assertEqual(answer["notes"]["synthetic_point_entities"], ["A", "B"])
        self.assertEqual(answer["entity_predictions"][0]["interval"], {"level": 0.9, "lo": 0.0, "hi": 1.0})
        report = self.suite.compare(answer)
        self.assertIsNone(report["interval_coverage"])
        self.assertEqual(report["official_interval_leg"], "disabled_pure_label")

    def test_realized_credit_events_are_not_probability_truth(self):
        self.task["family"] = "credit_event"
        self.task["target"]["name"] = "credit_event_12m"
        for row in self.refs:
            row["unit"] = "realized_event_indicator"
        self.refs[1]["reference_value"] = 0.0
        self.build_bundle()
        answer = self.suite.fixture(self.task_id, half_width=3.0)
        self.assertEqual(answer["notes"]["synthetic_point_entities"], ["A", "B"])
        for row in answer["entity_predictions"]:
            self.assertEqual(row["point_forecast"], 0.5)
            self.assertEqual(row["interval"], {"level": 0.9, "lo": 0.0, "hi": 1.0})
        report = self.suite.compare(answer)
        self.assertEqual(report["classification_accuracy"], 1.0)
        self.assertEqual(report["numeric_count"], 0)
        self.assertIsNone(report["mean_absolute_error"])
        self.assertIsNone(report["mean_interval_score_90"])
        self.assertEqual(report["entities"][0]["reference_value_kind"], "observed_event_indicator")

    def test_credit_probability_semantics_require_unit_interval(self):
        self.task["family"] = "credit_event"
        self.task["target"]["name"] = "credit_event_12m"
        self.build_bundle()
        original = self.answer()
        for change in ({"point_forecast": -0.1}, {"point_forecast": 1.1},
                       {"interval": {"level": 0.9, "lo": -0.1, "hi": 1.0}},
                       {"interval": {"level": 0.9, "lo": 0.0, "hi": 1.1}}):
            answer = copy.deepcopy(original)
            answer["entity_predictions"][0].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(SuiteError, "概率"):
                self.suite.validate(answer)
        del original["entity_predictions"][0]["point_forecast"]
        with self.assertRaisesRegex(SuiteError, "概率"):
            self.suite.validate(original)

    def test_compare_refuses_overflowing_derived_metric(self):
        answer = self.answer()
        answer["entity_predictions"][0]["point_forecast"] = -1e308
        self.refs[0]["reference_value"] = 1e308
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "absolute_error 必须为有限"):
            self.suite.compare(answer)

    def test_ranking_uses_metric_values_with_tie_aware_spearman(self):
        self.build_bundle("ranking")
        answer = self.answer()
        self.assertEqual(self.suite.compare(answer)["ranking"]["spearman_rho"], 1.0)
        answer["entity_predictions"][0]["point_forecast"] = 3.0
        self.assertEqual(self.suite.compare(answer)["ranking"]["spearman_rho"], -1.0)
        answer["entity_predictions"][1]["point_forecast"] = 3.0
        self.assertEqual(self.suite.compare(answer)["ranking"]["spearman_rho"], 0.0)
        self.assertAlmostEqual(spearman([1, 1, 2], [1, 2, 3]), math.sqrt(3) / 2)

    def test_ranking_partial_reference_never_reports_partial_rho(self):
        self.build_bundle("ranking")
        answer = self.answer()
        self.refs[0]["status"] = "provisional"
        self.build_bundle()
        self.assertFalse(self.suite.compare(answer)["ranking"]["complete_roster"])
        self.assertIsNone(self.suite.compare(answer)["ranking"]["spearman_rho"])

    def test_rank_requires_complete_permutation(self):
        self.build_bundle("ranking")
        original = self.answer()
        original["entity_predictions"][0]["rank"] = 1
        with self.assertRaisesRegex(SuiteError, "排列"):
            self.suite.validate(original)
        original["entity_predictions"][1]["rank"] = 1
        with self.assertRaisesRegex(SuiteError, "排列"):
            self.suite.validate(original)

    def test_rank_semantics_keep_strict_integer_even_for_whole_float(self):
        self.build_bundle("ranking")
        answer = self.answer()
        answer["entity_predictions"][0]["rank"] = 1.0
        answer["entity_predictions"][1]["rank"] = 2
        with self.assertRaisesRegex(SuiteError, "rank 必须为整数"):
            self.suite.validate(answer)

    def test_regression_cannot_omit_point_forecast(self):
        self.build_bundle("regression")
        answer = self.answer()
        del answer["entity_predictions"][0]["point_forecast"]
        with self.assertRaisesRegex(SuiteError, "缺少 point_forecast"):
            self.suite.validate(answer)

    def test_unknown_schema_keyword_cannot_silently_pass(self):
        self.schema["additionalProperties"] = False
        self.build_bundle()
        with self.assertRaisesRegex(SuiteError, "未实现"):
            self.answer()

    def test_source_without_https_or_locator_fails_audit(self):
        self.refs[0]["sources"][0]["locator"] = ""
        self.write_refs()
        with self.assertRaisesRegex(SuiteError, "可定位"):
            ReferenceSuite(self.root)

    def test_duplicate_json_object_fields_are_refused(self):
        with self.assertRaisesRegex(SuiteError, "重复字段"):
            parse_json('{"task_id": "x", "task_id": "y"}')

    def test_cli_audit_fixture_validate_compare_and_failure_exit(self):
        prefix = ["--data-root", str(self.root)]
        output = self.root / "test-output/answer.json"
        audit_output = self.root / "test-output/audit.json"
        commands = (["audit", "--expected-records", "2", "--expected-tasks", "1", "--output", str(audit_output)],
                    ["fixture", "--task-id", self.task_id, "--output", str(output)],
                    ["validate", "--answer", str(output)], ["compare", "--answer", str(output)])
        for command in commands:
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(prefix + command), 0)
                self.assertIsInstance(json.loads(stdout.getvalue()), dict)
        self.assertTrue(json.loads(audit_output.read_text())["ok"])
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(main(prefix + ["fixture", "--task-id", "unknown", "--output", str(output)]), 2)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])

    def test_cli_nonobject_supplied_task_returns_structured_failure(self):
        path = self.root / "invalid-task.json"
        self.dump(path, [])
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            code = main(["--data-root", str(self.root), "fixture", "--task", str(path),
                         "--output", str(self.root / "answer.json")])
        self.assertEqual(code, 2)
        self.assertIn("JSON 对象", json.loads(stderr.getvalue())["error"])

    def test_cli_batch_requires_complete_suite_unless_partial_is_explicit(self):
        first_answer = self.answer()
        second_id = "t4-second-test"
        second_unit = self.root / "inputs/units" / second_id
        shutil.copytree(self.unit, second_unit)
        second_task = copy.deepcopy(self.task)
        second_task["task_id"] = second_id
        self.dump(second_unit / "task.json", second_task)
        manifest_path = self.root / "inputs/source-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["units"].append({"task_id": second_id, "task_path": f"units/{second_id}/task.json",
                                 "task_sha256": hashlib.sha256((second_unit / "task.json").read_bytes()).hexdigest(),
                                 "task_canonical_sha256": canonical_hash(second_task),
                                 "files": [{"path": str(p.relative_to(self.root / "inputs")),
                                            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                           for p in second_unit.rglob("*") if p.is_file()]})
        self.dump(manifest_path, manifest)
        second_refs = copy.deepcopy(self.refs)
        for row in second_refs:
            row["task_id"] = second_id
            row["task_canonical_sha256"] = canonical_hash(second_task)
        self.refs.extend(second_refs)
        self.write_refs()
        suite = ReferenceSuite(self.root)
        answers = self.root / "batch"
        self.dump(answers / self.task_id / "answer.json", first_answer)
        report_path = self.root / "batch-report.json"
        for command in ("validate", "compare"):
            args = ["--data-root", str(self.root), command, "--answers-dir", str(answers),
                    "--output", str(report_path)]
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(args), 2)
            report = json.loads(stdout.getvalue())
            self.assertFalse(report["ok"])
            self.assertFalse(report["complete"])
            self.assertEqual(report["missing_tasks"], [second_id])
            self.assertEqual(json.loads(report_path.read_text()), report)
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(args + ["--allow-partial"]), 0)
            self.assertTrue(json.loads(stdout.getvalue())["ok"])
            self.assertFalse(json.loads(stdout.getvalue())["complete"])
        self.dump(answers / second_id / "answer.json", suite.fixture(second_id))
        for command in ("validate", "compare"):
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(["--data-root", str(self.root), command,
                                       "--answers-dir", str(answers)]), 0)
            report = json.loads(stdout.getvalue())
            self.assertTrue(report["ok"])
            self.assertTrue(report["complete"])
            self.assertEqual(report["task_count"], 2)
            self.assertEqual(report["missing_tasks"], [])


if __name__ == "__main__":
    unittest.main()
