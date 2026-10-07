"""错误输入与污染防线，用合成 task/corpus，不使用历史答案。"""
from copy import deepcopy
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
sys.path.insert(0, str(AGENT))
import candidate
from candidate import CandidateInputError, load_corpus, run, validate_answer
from contracts.task_table import task_table_text


class AgentFirewallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.input = self.base / "input"
        self.corpus = self.input / "corpus"
        self.corpus.mkdir(parents=True)
        self.task = {"task_id": "synthetic", "cutoff_date": "2024-01-31",
            "target": {"type": "classification", "labels": ["beat", "miss", "inline"]},
            "entities": [{"entity_id": "AAA", "name": "Issuer Alpha", "consensus_eps": 1.0,
                          "threshold_pct": 0.05, "corpus_ref": "corpus/"}]}
        self.task_path = self.input / "task.json"
        self.output = self.base / "output/answer.json"
        self.docs = {"AAA_EARNINGS": {"doc_id": "AAA_EARNINGS", "doc_date": "2024-01-15",
                     "text": "Issuer Alpha reported earnings per share of $1.50 for the earlier quarter."}}
        self.labels = {"AAA_EARNINGS": {"entity_ids": ["AAA"]}}
        self.write_inputs()

    @staticmethod
    def dump(path, obj):
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    def write_inputs(self):
        self.dump(self.task_path, self.task)
        files = []
        for did, doc in self.docs.items():
            path = self.corpus / (did + ".json")
            self.dump(path, doc)
            files.append({"path": "corpus/" + path.name, "role": "corpus",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **self.labels[did]})
        self.dump(self.corpus / "manifest.json", {"files": files})

    def answer(self):
        return run(self.task_path, self.corpus, self.output)

    def rejected(self, pattern=None):
        with self.assertRaises(CandidateInputError) as context:
            self.answer()
        if pattern:
            self.assertIn(pattern, str(context.exception))
        self.assertFalse(self.output.exists())

    def test_grounded_eps_rule_and_literal_claim(self):
        row = self.answer()["entity_predictions"][0]
        self.assertEqual(row["label"], "beat")
        self.assertEqual(row["point_forecast"], 1.5)
        self.assertEqual(row["claims"][0]["claim"], self.docs["AAA_EARNINGS"]["text"])

    def test_post_cutoff_text_never_reaches_reader(self):
        self.docs["AAA_EARNINGS"]["doc_date"] = "2024-02-01"
        self.write_inputs()
        row = self.answer()["entity_predictions"][0]
        self.assertEqual(row["label"], "inline")
        self.assertEqual(row["point_forecast"], 1.0)
        self.assertEqual(row["claims"][0]["doc_id"], "task")

    def test_wrong_entity_text_never_reaches_reader(self):
        self.labels["AAA_EARNINGS"] = {"entity_ids": ["OTHER"]}
        self.write_inputs()
        row = self.answer()["entity_predictions"][0]
        self.assertEqual(row["label"], "inline")
        self.assertEqual(row["claims"][0]["doc_id"], "task")

    def test_shared_document_is_admitted(self):
        self.labels["AAA_EARNINGS"] = {"shared": True}
        self.write_inputs()
        self.assertEqual(self.answer()["entity_predictions"][0]["label"], "beat")

    def test_unmanifested_answer_bait_is_not_read(self):
        self.dump(self.corpus / "reference.json", {"secret": "future resolved answer"})
        self.dump(self.input / "reference.jsonl", {"label": "miss"})
        real_open, reads = candidate.os.open, []
        def record(path, *args, **kwargs):
            reads.append(Path(path))
            return real_open(path, *args, **kwargs)
        with patch.object(candidate.os, "open", side_effect=record):
            self.assertEqual(self.answer()["entity_predictions"][0]["label"], "beat")
        self.assertEqual(set(reads), {self.task_path, self.corpus / "manifest.json",
                                     self.corpus / "AAA_EARNINGS.json"})

    def test_duplicate_json_key_rejected(self):
        self.task_path.write_text('{"task_id":"a","task_id":"b"}')
        self.rejected("Duplicate JSON key")

    def test_nonfinite_json_constants_rejected(self):
        self.task["entities"][0]["consensus_eps"] = float("nan")
        self.write_inputs()
        self.rejected("Non-finite")

    def test_exponent_overflow_rejected(self):
        self.task_path.write_text(json.dumps(self.task).replace('"consensus_eps": 1.0',
                                                               '"consensus_eps": 1e999'))
        self.rejected("Non-finite")

    def test_integer_outside_float_range_rejected(self):
        self.task["entities"][0]["consensus_eps"] = 10 ** 500
        self.write_inputs()
        self.rejected("Non-finite")

    def test_object_target_type_rejected(self):
        self.task["target"]["type"] = {"bad": True}
        self.write_inputs()
        self.rejected("target type")

    def test_invalid_cutoff_calendar_rejected(self):
        self.task["cutoff_date"] = "2024-02-31"
        self.write_inputs()
        self.rejected("calendar date")

    def test_undated_corpus_rejected(self):
        del self.docs["AAA_EARNINGS"]["doc_date"]
        self.write_inputs()
        self.rejected("doc_date")

    def test_duplicate_entity_rejected(self):
        self.task["entities"].append(deepcopy(self.task["entities"][0]))
        self.write_inputs()
        self.rejected("Entity IDs")

    def test_bad_label_vocabulary_rejected(self):
        self.task["target"]["labels"] = ["same", "same"]
        self.write_inputs()
        self.rejected("Classification labels")

    def test_conflicting_target_type_rejected(self):
        self.task["target_type"] = "regression"
        self.write_inputs()
        self.rejected("Conflicting")

    def test_unsupported_corpus_ref_rejected(self):
        self.task["entities"][0]["corpus_ref"] = "../private-evidence/"
        self.write_inputs()
        self.rejected("corpus_ref")

    def test_boolean_numeric_feature_rejected(self):
        self.task["entities"][0]["consensus_eps"] = True
        self.write_inputs()
        self.rejected("numeric")

    def test_negative_threshold_rejected(self):
        self.task["entities"][0]["threshold_pct"] = -0.05
        self.write_inputs()
        self.rejected("non-negative")

    def test_hash_mismatch_rejected(self):
        self.dump(self.corpus / "AAA_EARNINGS.json", {"tampered": True})
        self.rejected("SHA-256 mismatch")

    def test_manifest_path_traversal_rejected(self):
        path = self.corpus / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["files"][0]["path"] = "corpus/../private.json"
        self.dump(path, manifest)
        self.rejected("manifest path")

    def test_corpus_leaf_symlink_rejected(self):
        path = self.corpus / "AAA_EARNINGS.json"
        real = self.base / "elsewhere.json"
        path.rename(real)
        path.symlink_to(real)
        self.rejected("symlink")

    def test_corpus_directory_symlink_rejected(self):
        link = self.base / "corpus-link"
        link.symlink_to(self.corpus, target_is_directory=True)
        with self.assertRaises(CandidateInputError):
            run(self.task_path, link, self.output)

    def test_task_symlink_rejected(self):
        real = self.input / "actual-task.json"
        self.task_path.rename(real)
        self.task_path.symlink_to(real)
        self.rejected("symlink")

    def test_doc_id_filename_mismatch_rejected(self):
        self.docs["AAA_EARNINGS"]["doc_id"] = "EVIL"
        self.write_inputs()
        self.rejected("doc_id")

    def test_invalid_spans_rejected(self):
        self.docs["AAA_EARNINGS"].pop("text")
        self.docs["AAA_EARNINGS"]["spans"] = [{"text": 5}]
        self.write_inputs()
        self.rejected("spans")

    def test_flat_text_and_joined_span_offsets(self):
        self.docs["AAA_EARNINGS"].pop("text")
        self.docs["AAA_EARNINGS"]["spans"] = [{"text": "Issuer Alpha reported"},
                                              {"text": "earnings per share of $1.50."}]
        self.write_inputs()
        claim = self.answer()["entity_predictions"][0]["claims"][0]
        self.assertEqual(claim["claim"], "Issuer Alpha reported earnings per share of $1.50.")
        self.assertEqual(claim["span_end"], len(claim["claim"]))

    def test_output_inside_input_rejected(self):
        original = self.task_path.read_bytes()
        with self.assertRaises(CandidateInputError):
            run(self.task_path, self.corpus, self.task_path)
        self.assertEqual(self.task_path.read_bytes(), original)

    def test_wrong_own_row_fallback_rejected(self):
        self.task["entities"].append({"entity_id": "BBB", "name": "Issuer Beta", "corpus_ref": "corpus/"})
        self.docs.clear()
        self.write_inputs()
        answer = self.answer()
        answer["entity_predictions"][1]["claims"] = answer["entity_predictions"][0]["claims"]
        with self.assertRaisesRegex(CandidateInputError, "own row"):
            validate_answer(answer, self.task, [])

    def test_nonliteral_output_claim_rejected(self):
        answer = self.answer()
        answer["entity_predictions"][0]["claims"][0]["claim"] = "Future earnings are known."
        with self.assertRaisesRegex(CandidateInputError, "exact"):
            validate_answer(answer, self.task, load_corpus(self.corpus))

    def test_nonfinite_output_rejected(self):
        answer = self.answer()
        answer["entity_predictions"][0]["point_forecast"] = float("inf")
        with self.assertRaisesRegex(CandidateInputError, "finite"):
            validate_answer(answer, self.task, load_corpus(self.corpus))

    def test_cli_input_error_is_nonzero_and_does_not_write(self):
        self.task_path.write_text("not JSON")
        proc = subprocess.run([sys.executable, str(AGENT / "analyze.py"), "analyze", "--task",
            str(self.task_path), "--corpus", str(self.corpus), "--out", str(self.output)],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("rejected", proc.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
