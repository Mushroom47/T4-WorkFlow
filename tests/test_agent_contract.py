"""候选入口、公开单位与封装边界；不读取参考答案或 outcome。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
UNITS = ROOT / "datasets/agenthon-t4-reference/inputs/units"
sys.path.insert(0, str(AGENT))
from candidate import CandidateInputError, is_probability_target, load_corpus, run, validate_answer
from contracts.task_table import task_table_text


class AgentContractTests(unittest.TestCase):
    def test_all_eleven_units_real_argv_and_frozen_inputs(self):
        tasks = sorted(UNITS.glob("*/task.json"))
        self.assertEqual(len(tasks), 11)
        files = [p for p in UNITS.rglob("*") if p.is_file()]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        entities, types = 0, set()
        with tempfile.TemporaryDirectory() as temp:
            for task_path in tasks:
                with self.subTest(unit=task_path.parent.name):
                    output = Path(temp) / task_path.parent.name / "answer.json"
                    proc = subprocess.run([sys.executable, str(AGENT / "analyze.py"), "analyze",
                        "--task", str(task_path), "--corpus", str(task_path.parent / "corpus"),
                        "--out", str(output)], capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertFalse(output.read_bytes().startswith(b"\xef\xbb\xbf"))
                    answer = json.loads(output.read_text())
                    task = json.loads(task_path.read_text())
                    self.assertEqual(answer["task_id"], task["task_id"])
                    self.assertEqual([r["entity_id"] for r in answer["entity_predictions"]],
                                     [r["entity_id"] for r in task["entities"]])
                    validate_answer(answer, task, load_corpus(task_path.parent / "corpus"))
                    entities += len(answer["entity_predictions"])
                    types.add(answer["target_type"])
        self.assertEqual(entities, 78)
        self.assertEqual(types, {"classification", "regression", "ranking"})
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_optional_verb_for_local_usage(self):
        task = UNITS / "t4-EXAMPLE-eps-beat/task.json"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "answer.json"
            proc = subprocess.run([sys.executable, str(AGENT / "analyze.py"), "--task", str(task),
                "--corpus", str(task.parent / "corpus"), "--out", str(output)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(output.exists())

    def test_wrong_verb_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "answer.json"
            proc = subprocess.run([sys.executable, str(AGENT / "analyze.py"), "simulate",
                "--task", "/missing/task.json", "--corpus", "/missing/corpus", "--out", str(output)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(output.exists())

    def test_deterministic_output(self):
        task = UNITS / "t4-credit-event-2023/task.json"
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a.json", Path(temp) / "b.json"
            run(task, task.parent / "corpus", a)
            run(task, task.parent / "corpus", b)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_frozen_credit_probability_output_passes_suite_without_reference_answers(self):
        # ReferenceSuite.validate uses input manifests/schema/corpus only. Its
        # constructor normally also loads reference records for comparison;
        # intercept that exact file as empty so this regression cannot see them.
        from tools.reference_suite import ReferenceSuite
        data = UNITS.parents[1]
        task_path = UNITS / "t4-credit-event-2023/task.json"
        original_read_text = Path.read_text
        reads = []
        def input_only_read(path, *args, **kwargs):
            if path.resolve() == (data / "reference.jsonl").resolve():
                return ""
            reads.append(path)
            return original_read_text(path, *args, **kwargs)
        with tempfile.TemporaryDirectory() as temp:
            answer = run(task_path, task_path.parent / "corpus", Path(temp) / "answer.json")
            with patch.object(Path, "read_text", input_only_read):
                suite = ReferenceSuite(data)
                result = suite.validate(answer)
            self.assertTrue(result["ok"])
            self.assertEqual(result["entity_count"], 8)
            self.assertEqual(suite.records, [])
            self.assertNotIn(data / "reference.jsonl", reads)
            for row in answer["entity_predictions"]:
                self.assertEqual(row["point_forecast"], 0.5)
                self.assertEqual(row["interval"], {"level": 0.9, "lo": 0.0, "hi": 1.0})
                self.assertEqual(row["label"], "credit_event")  # 0.5 tie, task vocabulary order.

    def test_probability_validation_rejects_outside_center_and_bounds(self):
        task_path = UNITS / "t4-credit-event-2023/task.json"
        task = json.loads(task_path.read_text())
        docs = load_corpus(task_path.parent / "corpus")
        with tempfile.TemporaryDirectory() as temp:
            for point, lo, hi in ((-0.01, 0.0, 1.0), (1.01, 0.0, 1.0),
                                  (0.5, -0.01, 1.0), (0.5, 0.0, 1.01), (0.5, 0.6, 1.0)):
                with self.subTest(point=point, lo=lo, hi=hi):
                    answer = run(task_path, task_path.parent / "corpus", Path(temp) / "answer.json")
                    row = answer["entity_predictions"][0]
                    row["point_forecast"] = point
                    row["interval"].update(lo=lo, hi=hi)
                    with self.assertRaisesRegex(CandidateInputError, "Probability"):
                        validate_answer(answer, task, docs)

    def test_probability_detection_reads_contract_not_task_ids(self):
        self.assertTrue(is_probability_target({"task_id": "unknown-new-unit",
            "target": {"type": "classification"},
            "prompt": "point_forecast = your predicted PROBABILITY of an event (0 to 1)."}))
        self.assertTrue(is_probability_target({"target": {"type": "regression", "unit": "probability"}}))
        self.assertFalse(is_probability_target({"family": "credit_event", "target": {"name": "credit_event_12m"}}))
        self.assertFalse(is_probability_target({"prompt": "point_forecast is a dollar amount, not a probability."}))

    def test_missing_index_uses_own_task_row(self):
        task_path = UNITS / "t4-EXAMPLE-eps-beat/task.json"
        with tempfile.TemporaryDirectory() as temp:
            answer = run(task_path, task_path.parent / "corpus", Path(temp) / "answer.json")
            claim = answer["entity_predictions"][0]["claims"][0]
            table, ranges = task_table_text(json.loads(task_path.read_text()))
            self.assertEqual(claim["doc_id"], "task")
            self.assertEqual(claim["claim"], table[claim["span_start"]:claim["span_end"]])
            self.assertEqual(claim["span_start"], ranges["AAPL"][0])

    def test_vendor_files_match_frozen_digests(self):
        manifest = json.loads((AGENT / "upstream-manifest.json").read_text())
        self.assertEqual(manifest["upstream_commit"], "1c744e1d6725340643a533f436517d72b53ca0e1")
        self.assertEqual(manifest["license"], "MIT")
        for item in manifest["files"]:
            raw = (AGENT / item["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(len(raw), item["bytes"])
            self.assertFalse(item["modified"])

    def test_dockerfile_has_explicit_code_only_copy_and_contract(self):
        docker = (AGENT / "Dockerfile").read_text()
        self.assertIn('LABEL qfbench2.interface_version="2.0"', docker)
        self.assertIn('ENTRYPOINT ["python", "analyze.py"]', docker)
        self.assertIn("FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c", docker)
        instructions = [line.split()[0].upper() for line in docker.splitlines()
                        if line.strip() and not line.lstrip().startswith("#")]
        self.assertNotIn("VOLUME", instructions)
        for line in docker.splitlines():
            if line.startswith("COPY "):
                self.assertNotIn("COPY . ", line)
                self.assertNotIn("reference", line)
                self.assertNotIn("datasets", line)
                self.assertNotIn(".local", line)
        self.assertEqual((AGENT / ".dockerignore").read_text().splitlines()[0], "**")


if __name__ == "__main__":
    unittest.main()
