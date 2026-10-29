"""Regression checks for leakage, weighted scoring and the real feature boundary."""
import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "lightweight_cv"))
spec = importlib.util.spec_from_file_location("lightweight_pipeline", HERE / "lightweight_cv" / "pipeline.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class WordTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(m.start(), m.end()) for m in p.re.finditer(r"\S+", text)]}


class FakeEncoder:
    tokenizer = WordTokenizer()

    def encode(self, texts):
        self.inputs = texts
        vectors = []
        for text in texts:
            value = np.array([text.lower().count(word) for word in ("python", "paid", "project", "never")], dtype=np.float32) + 0.1
            vectors.append(value / np.linalg.norm(value))
        return np.array(vectors)


def fixture():
    return {"sample_id": "fixture", "cv_text": "I have never used Python in paid work.\nIndependent project using Python.",
            "requirements": [{"id": "r1", "text": "Paid Python experience", "weight": 3},
                             {"id": "r2", "text": "Python project", "weight": 2}]}


class LightweightTests(unittest.TestCase):
    def test_documented_score_is_72_point_22(self):
        requirements = [{"id": f"r{i}", "weight": w} for i, w in enumerate([3, 2, 2, 2])]
        result = p.weighted_score(requirements, dict(zip([r["id"] for r in requirements], ["partial", "met", "met", "partial"])))
        self.assertAlmostEqual(result, 100 * 6.5 / 9)

    def test_no_silent_missing_or_duplicate_ids(self):
        with self.assertRaises(ValueError):
            p.weighted_score(fixture()["requirements"], {"r1": "met"})
        sample = fixture()
        sample["requirements"][1]["id"] = "r1"
        with self.assertRaises(ValueError):
            p.validate_input(sample)

    def test_boolean_weight_is_rejected(self):
        sample = fixture()
        sample["requirements"][0]["weight"] = True
        with self.assertRaises(ValueError):
            p.validate_input(sample)

    def test_feature_builder_never_reads_gold_or_weight(self):
        sample = fixture()
        encoder = FakeEncoder()
        before, _ = p.features_for_samples([sample], encoder)
        sample.update(target={"assessments": "GOLD_SECRET"}, cv_group="GROUP_SECRET")
        sample["requirements"][0]["weight"] = 5
        after, _ = p.features_for_samples([sample], encoder)
        np.testing.assert_array_equal(before, after)
        self.assertNotIn("GOLD_SECRET", str(encoder.inputs))
        self.assertNotIn("GROUP_SECRET", str(encoder.inputs))
        self.assertTrue(any(t.startswith("query: ") for t in encoder.inputs))
        self.assertTrue(any(t.startswith("passage: ") for t in encoder.inputs))

    def test_chunking_keeps_negation_and_original_offsets(self):
        text = "  I have never used Python.\r\n" + " ".join(f"token{i}" for i in range(450))
        chunks = p.chunk_cv(text, WordTokenizer())
        self.assertIn("never", chunks[0]["text"])
        for chunk in chunks:
            self.assertEqual(text[chunk["start"]:chunk["end"]], chunk["text"])
        self.assertIn("token449", chunks[-1]["text"])

    def test_template_counts_and_contributions_agree(self):
        sample = fixture()
        _, records = p.features_for_samples([sample], FakeEncoder())
        review = p.render_review(sample, {"r1": "partial", "r2": "met"}, records)
        self.assertEqual(review["score"], 70.0)
        self.assertIn("1/2", review["summary"])
        self.assertIn("1 đáp ứng một phần", review["summary"])
        self.assertAlmostEqual(sum(a["contribution_points"] for a in review["assessments"]), review["score"])
        self.assertNotIn("đã dùng Python", review["summary"])

    def test_modified_retrieval_cannot_be_presented_as_verbatim(self):
        sample = fixture()
        _, records = p.features_for_samples([sample], FakeEncoder())
        records[0]["retrieved"][0]["text"] = "Invented paid employment."
        with self.assertRaises(ValueError):
            p.render_review(sample, {"r1": "partial", "r2": "met"}, records)

    def test_group_leakage_is_rejected_before_flattening(self):
        splits, _ = p.load_splits(HERE / "datasets" / "cvai_v1")
        with tempfile.TemporaryDirectory() as directory:
            splits["validation"][0]["cv_group"] = splits["train"][0]["cv_group"]
            for name, rows in splits.items():
                (Path(directory) / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Leakage cv_group"):
                p.load_splits(directory)

    def test_numeric_export_matches_sklearn(self):
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            from sklearn.neural_network import MLPClassifier
        except ImportError:
            self.skipTest("Install lightweight_cv/requirements.txt")
        rng = np.random.default_rng(42)
        x = rng.normal(size=(60, 8)).astype(np.float32)
        y = np.array(list(p.LABELS) * 20)
        scaler = StandardScaler().fit(x)
        for classifier in (LogisticRegression(), MLPClassifier(hidden_layer_sizes=(6,), solver="lbfgs", max_iter=1000, random_state=42)):
            classifier.fit(scaler.transform(x), y)
            with tempfile.TemporaryDirectory() as directory:
                artifact = Path(directory) / "head.npz"
                p.save_classifier(artifact, scaler, classifier)
                np.testing.assert_array_equal(p.ClassifierHead(artifact).predict(x), classifier.predict(scaler.transform(x)))

    def test_weight_changes_score_but_not_prediction_features(self):
        sample = fixture()
        statuses = {"r1": "not_evidenced", "r2": "met"}
        before = p.weighted_score(sample["requirements"], statuses)
        sample["requirements"][0]["weight"] = 5
        self.assertLess(p.weighted_score(sample["requirements"], statuses), before)

    def test_invalid_artifact_rejected_without_model_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"feature_version": p.FEATURE_VERSION, "mode": "smoke"}))
            with self.assertRaisesRegex(ValueError, "full"):
                p.Reviewer(root)

    def test_notebook_cells_compile(self):
        notebook = json.loads((HERE / "lightweight_cv/train_e5_classifier.ipynb").read_text(encoding="utf-8"))
        for item in notebook["cells"]:
            if item["cell_type"] == "code":
                compile("".join(item["source"]), item["id"], "exec")


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if importlib.util.find_spec("fastapi") is None:
            self.skipTest("Install lightweight_cv/requirements.txt")
        spec = importlib.util.spec_from_file_location("lightweight_server", HERE / "lightweight_cv/server.py")
        self.server = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"pipeline": p}):
            spec.loader.exec_module(self.server)
        self.server.app.state.key = "x" * 32
        self.server.app.state.busy = False
        self.body = self.server.Request.model_validate(fixture())

    async def test_bad_key_and_busy_are_rejected(self):
        with self.assertRaises(self.server.HTTPException) as caught:
            await self.server.review(self.body, "bad-key")
        self.assertEqual(caught.exception.status_code, 401)
        self.server.app.state.busy = True
        with self.assertRaises(self.server.HTTPException) as caught:
            await self.server.review(self.body, "x" * 32)
        self.assertEqual(caught.exception.status_code, 429)

    async def test_invalid_input_releases_slot(self):
        class InvalidReviewer:
            def review(self, sample):
                raise ValueError("Duplicate ID")
        self.server.app.state.reviewer = InvalidReviewer()
        with self.assertRaises(self.server.HTTPException) as caught:
            await self.server.review(self.body, "x" * 32)
        self.assertEqual(caught.exception.status_code, 422)
        self.assertFalse(self.server.app.state.busy)

    async def test_raw_jd_and_prepared_profile_request_contracts(self):
        from pydantic import ValidationError
        raw = self.server.Request.model_validate({"cv_text": "Python", "jd_text": "Python required."})
        self.assertIsNone(raw.requirements)
        with self.assertRaises(ValidationError):
            self.server.Request.model_validate({"cv_text": "Python", "jd_text": "Python required.", "requirements": fixture()["requirements"]})
        with self.assertRaises(ValidationError):
            self.server.Request.model_validate({"cv_text": "Python"})
        profile = await self.server.prepare_job(self.server.JDRequest(jd_text="Python required."), "x" * 32)
        self.assertEqual(profile["status"], "ready")
        saved = self.server.Request.model_validate({"cv_text": "Python", "job_profile": profile})
        self.assertEqual(saved.job_profile["profile_id"], profile["profile_id"])

    async def test_prepare_endpoint_protected_and_returns_unresolved(self):
        body = self.server.JDRequest(jd_text="Python or Java required.")
        with self.assertRaises(self.server.HTTPException) as caught:
            await self.server.prepare_job(body, "wrong")
        self.assertEqual(caught.exception.status_code, 401)
        profile = await self.server.prepare_job(body, "x" * 32)
        self.assertEqual(profile["status"], "needs_review")

    async def test_unsupported_jd_returns_profile_without_score(self):
        from jd_parser import JDPreparationError, prepare_jd
        class UnresolvedReviewer:
            def review(self, sample):
                raise JDPreparationError(prepare_jd(sample["jd_text"]))
        self.server.app.state.reviewer = UnresolvedReviewer()
        body = self.server.Request(cv_text="Python", jd_text="Python or Java required.")
        with self.assertRaises(self.server.HTTPException) as caught:
            await self.server.review(body, "x" * 32)
        self.assertEqual(caught.exception.status_code, 422)
        self.assertEqual(caught.exception.detail["jd_profile"]["status"], "needs_review")
        self.assertNotIn("score", caught.exception.detail)

    async def test_cancelled_request_keeps_slot_until_cpu_work_finishes(self):
        import threading
        started, finish = threading.Event(), threading.Event()
        class SlowReviewer:
            def review(self, sample):
                started.set()
                finish.wait(timeout=5)
                return {"score": 0}
        self.server.app.state.reviewer = SlowReviewer()
        task = asyncio.create_task(self.server.review(self.body, "x" * 32))
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        self.assertTrue(started.is_set())
        task.cancel()
        await asyncio.sleep(0.01)
        self.assertTrue(self.server.app.state.busy)
        finish.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(self.server.app.state.busy)


if __name__ == "__main__":
    unittest.main()
