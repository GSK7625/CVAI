"""Semantic invariants and safety boundaries of the new feature path."""
import copy
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from evidence_features import (FEATURE_NAMES, analyze, annotate_review, duration_evidence,
                               requirement_spec, rule_label, structured_features)


class EvidenceTests(unittest.TestCase):
    def test_selection_uses_per_kind_validation_gates(self):
        from optimize_evidence import choose
        def row(name, f1, paid, dimension=61):
            val = {"macro_f1": f1, "by_kind": {k: {"accuracy": paid if k == "professional" else .9}
                   for k in ("basic", "practical", "professional", "experience")}}
            return {"name": name, "old_validation": val, "new_validation": val,
                    "dimension": dimension, "minimal_pairs": False}
        baseline = row("base", .7, .8)
        bad = row("bad", .99, .75)
        good = row("good", .8, .85)
        self.assertEqual(choose([bad, good], [baseline])["name"], "good")
        self.assertIsNone(choose([bad], [baseline]))

    def test_bootstrap_is_paired_and_identical_models_have_zero_delta(self):
        from evaluate_evidence import paired_bootstrap
        samples = [{"sample_id": str(i), "cv_group": str(i), "jd_group": str(i//2),
                    "requirements": [{"id": "r1", "weight": 3}],
                    "target": {"assessments": [{"id": "r1", "status": "met"}]}} for i in range(8)]
        predicted = np.array(["met", "partial"] * 4)
        for method in ("jd", "crossed_jd_cv"):
            result = paired_bootstrap(samples, predicted, predicted, method, repeats=30)
            self.assertEqual(result["delta_f1_ci95"], [0, 0])
            self.assertEqual(result["delta_mae_ci95"], [0, 0])

    def test_holdout_api_check_sends_one_input_source(self):
        from evaluate_evidence import normalized_input
        from jd_parser import resolve_input
        sample = {"sample_id": "test", "cv_text": "Skills inventory: Python.",
                  "jd_text": "Some raw JD", "job_title": "Backend developer",
                  "requirements": [{"id": "r1", "text": "Basic familiarity with Python.", "weight": 1}],
                  "target": {"secret": "met"}}
        normalized, _ = resolve_input(normalized_input(sample))
        self.assertEqual(normalized["requirements"], sample["requirements"])
        self.assertNotIn("target", normalized)

    def test_minimal_context_pairs_change_required_strength(self):
        cv = "Independent project: used Python to implement a CSV importer."
        expected = [("Basic familiarity with Python.", "met"),
                    ("Project-level experience applying Python.", "met"),
                    ("Use Python during paid employment.", "partial")]
        for req, label in expected:
            self.assertEqual(rule_label(analyze(cv, req)), label)
        self.assertEqual(rule_label(analyze(cv.replace("Independent project", "Paid work"), expected[-1][0])), "met")

    def test_similar_names_do_not_supply_evidence(self):
        for cv, skill in [("Paid work: used JavaScript to build a UI.", "Java"),
                          ("Paid work: used React Native to build a screen.", "React"),
                          ("Paid work: used PostgreSQL to store data.", "SQL")]:
            self.assertEqual(rule_label(analyze(cv, f"Basic familiarity with {skill}.")), "not_evidenced")

    def test_negation_and_conflict_are_not_paid_evidence(self):
        req = "Use Python during paid employment."
        self.assertEqual(rule_label(analyze("I have not used Python in work or projects.", req)), "not_evidenced")
        result = analyze("Paid work: used Python to parse logs.\nI have not used Python.", req)
        self.assertIsNone(rule_label(result))
        self.assertIn("conflicting_skill_claims", result["review_reasons"])

    def test_mixed_entities_and_vague_team_claim_abstain(self):
        for cv in ["Paid work: used Python; SQL is only listed.",
                   "A team I belonged to mentioned SQL; my own use and work context are unspecified."]:
            self.assertIsNone(rule_label(analyze(cv, "Use SQL during paid employment.")))

    def test_month_union_role_scope_boundary_and_ambiguous_dates(self):
        cv = ("Paid backend developer, contract 1: 2021-01 to 2022-01 (end exclusive).\n"
              "Paid backend developer, contract 2: 2021-07 to 2022-07 (end exclusive).\n"
              "Paid frontend developer experience: 60 months.")
        self.assertEqual(duration_evidence(cv, "backend developer")["months"], 18)
        req = "At least 18 non-overlapping calendar months of paid backend developer work."
        self.assertEqual(requirement_spec(req)["kind"], "experience")
        self.assertEqual(rule_label(analyze(cv, req)), "met")
        self.assertEqual(rule_label(analyze(cv, req.replace("18", "19"))), "partial")
        self.assertIsNone(rule_label(analyze(cv.replace(" (end exclusive)", ""), req)))
        self.assertIsNone(rule_label(analyze("Paid backend developer: 12 months.\nPaid backend developer: 8 months.", req)))

    def test_features_never_read_label_id_weight_or_group(self):
        sample = {"cv_text": "Skills inventory: Python.", "requirements": [
            {"id": "r1", "text": "Basic familiarity with Python.", "weight": 1}]}
        x, _ = structured_features([sample])
        changed = copy.deepcopy(sample)
        changed.update(target={"secret": "met"}, cv_group="secret", jd_group="secret")
        changed["requirements"][0].update(id="secret", weight=5)
        y, _ = structured_features([changed])
        np.testing.assert_array_equal(x, y)
        self.assertEqual(x.shape[1], len(FEATURE_NAMES))

    def test_unresolved_review_does_not_publish_aggregate_points(self):
        analysis = analyze("Team mentioned Python.", "Use Python during paid employment.")
        result = {"score": 100, "assessments": [{"id": "r1", "contribution_points": 100}]}
        annotate_review(result, [analysis])
        self.assertEqual(result["status"], "needs_review")
        self.assertIsNone(result["score"])
        self.assertIsNone(result["assessments"][0]["contribution_points"])

    def test_common_renderer_applies_abstention_for_cli_and_evaluation(self):
        from pipeline import render_review
        sample = {"sample_id": "x", "cv_text": "Team mentioned Python.", "requirements": [
            {"id": "r1", "text": "Use Python during paid employment.", "weight": 3}]}
        record = {"requirement_id": "r1", "retrieved": [{"start": 0, "end": len(sample["cv_text"]),
                  "text": sample["cv_text"], "similarity": .9}],
                  "evidence_signals": analyze(sample["cv_text"], sample["requirements"][0]["text"])}
        result = render_review(sample, {"r1": "met"}, [record])
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "needs_review")


if __name__ == "__main__": unittest.main()
