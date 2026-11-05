import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from jd_parser_v2 import prepare_jd
from jd_review import review_with_diagnostics
from evidence_features import requirement_spec
from test_jd_parser_v2 import ML_JD


class ReviewerStub:
    def __init__(self, labels=None):
        self.calls = []
        self.labels = labels or {}

    def review(self, sample):
        self.calls.append(sample)
        assessments = []
        for req in sample["requirements"]:
            spec = requirement_spec(req["text"])
            if spec["kind"] == "unknown":
                raise AssertionError("Invalid input for frozen model: " + req["text"])
            label = self.labels.get(spec.get("skill", spec.get("role")), "met")
            assessments.append({"id": req["id"], "status": label or "met",
                                "evidence_signals": {"contexts": [], "review_reasons": [] if label else ["unresolved_skill_context"]}})
        return {"status": "ready", "score": 100, "assessments": assessments}


class JDReviewTests(unittest.TestCase):
    def review(self, jd, labels=None, **extra):
        reviewer = ReviewerStub(labels)
        result = review_with_diagnostics(reviewer, {"cv_text": "Skills: Python, Rust", "jd_text": jd, **extra})
        return result, reviewer

    def test_supported_jd_keeps_full_score(self):
        result, reviewer = self.review("Python required.")
        self.assertEqual(result["score"], 100)
        self.assertEqual(len(reviewer.calls), 1)

    def test_real_jd_reaches_model_without_changing_approximate_duration(self):
        result, reviewer = self.review(ML_JD, {"pandas": "partial", "SQL": "partial", "Apache Spark": "not_evidenced", "scikit-learn": "not_evidenced"})
        self.assertEqual(result["jd_profile"]["status"], "ready")
        self.assertEqual(len(result["assessments"]), 5)
        self.assertEqual(len(reviewer.calls[0]["requirements"]), 4)
        self.assertEqual(sum(a["status"] == "needs_review" for a in result["assessments"]), 1)
        self.assertIsNone(result["score"])
        self.assertTrue(all(a["contribution_points"] is None for a in result["assessments"]))

    def test_new_skill_is_extracted_but_not_sent_to_unsupported_model(self):
        result, reviewer = self.review("Python required.\nRust required.")
        self.assertEqual(result["jd_profile"]["status"], "ready")
        self.assertEqual(len(result["assessments"]), 2)
        self.assertEqual(len(reviewer.calls[0]["requirements"]), 1)
        self.assertIsNone(result["score"])
        self.assertIn("unsupported_skill", result["assessments"][1]["evidence_signals"]["review_reasons"])
        self.assertEqual(result["assessments"][1]["evidence_signals"]["contexts"][0]["text"], "Skills: Python, Rust")

    def test_or_takes_best_alternative_and_and_requires_both(self):
        labels = {"Python": "met", "Java": "not_evidenced"}
        self.assertEqual(self.review("Python or Java required.", labels)[0]["score"], 100)
        self.assertEqual(self.review("Python and Java required.", labels)[0]["score"], 50)

    def test_nested_groups_keep_semantics(self):
        result, _ = self.review("(Python and SQL) or Java required.", {"Python": "met", "SQL": "not_evidenced", "Java": "partial"})
        self.assertEqual(result["score"], 50)
        self.assertEqual(len(result["assessments"]), 1)

    def test_or_can_be_proven_despite_unknown_alternative(self):
        self.assertEqual(self.review("Python or Rust required.")[0]["score"], 100)
        self.assertIsNone(self.review("Python or Rust required.", {"Python": "partial"})[0]["score"])

    def test_uncertain_cv_context_is_not_accepted_as_met(self):
        result, _ = self.review("Python required.", {"Python": None})
        self.assertIsNone(result["score"])
        self.assertEqual(result["assessments"][0]["status"], "needs_review")

    def test_unsupported_conditions_do_not_get_partial_total(self):
        for clause in ["Good communication required.", "Advanced SQL required.", "English IELTS 6.5 required."]:
            with self.subTest(clause=clause):
                result, _ = self.review("Python required.\n" + clause)
                self.assertIsNone(result["score"])

    def test_minimum_role_duration_uses_compatible_model_rubric(self):
        result, reviewer = self.review("At least 2 years of paid experience as a backend developer.")
        self.assertEqual(result["score"], 100)
        self.assertIn("24 months", reviewer.calls[0]["requirements"][0]["text"])

    def test_explicit_exact_duration_satisfies_approximate_jd(self):
        cv = "Paid data/ML engineer experience: 4 months."
        result = review_with_diagnostics(ReviewerStub(), {"cv_text": cv, "jd_text": ML_JD})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["score"], 100)
        duration = next(a for a in result["assessments"] if a["assessment_method"] == "exact_duration_evidence")
        self.assertEqual(duration["status"], "met")
        self.assertEqual(duration["contribution_points"], 20)
        context = duration["evidence_signals"]["contexts"][0]
        self.assertEqual(cv[context["start"]:context["end"]], context["text"])
        self.assertEqual(result["jd_profile"]["criteria"][0]["duration"]["relation"], "approximate")

    def test_approximate_jd_requires_exact_relevant_unambiguous_evidence(self):
        cvs = ["Paid data/ML engineer experience: 3 months.",
               "Paid data/ML engineer experience: 5 months.",
               "Paid backend developer experience: 4 months.",
               "Unpaid data/ML engineer experience: 4 months.",
               "Paid data/ML engineer experience: about 4 months.",
               "Paid data/ML engineer experience: more than 4 months.",
               "Paid data/ML engineer experience: 3-4 months.",
               "Paid data/ML engineer experience: 1 year and 4 months.",
               "Paid data/ML engineer experience: 4 months.\nPaid data/ML engineer experience: 2 months."]
        for cv in cvs:
            with self.subTest(cv=cv):
                result = review_with_diagnostics(ReviewerStub(), {"cv_text": cv, "jd_text": ML_JD})
                self.assertIsNone(result["score"])
                self.assertEqual(result["assessments"][0]["status"], "needs_review")

    def test_weights_are_derived_from_jd(self):
        result, _ = self.review("Python required.\nJava preferred.", {"Python": "met", "Java": "not_evidenced"})
        self.assertEqual(result["score"], 75)

    def test_profile_reuse_and_tampering(self):
        profile = prepare_jd("Python required.")
        result = review_with_diagnostics(ReviewerStub(), {"cv_text": "Python", "job_profile": profile})
        self.assertEqual(result["score"], 100)
        edited = copy.deepcopy(profile)
        edited["criteria"][0]["weight"] = 1
        with self.assertRaises(ValueError):
            review_with_diagnostics(ReviewerStub(), {"cv_text": "Python", "job_profile": edited})

    def test_invalid_cv_and_ambiguous_input_are_rejected(self):
        for cv in [None, "   ", "x" * 30001]:
            with self.assertRaises(ValueError):
                review_with_diagnostics(ReviewerStub(), {"cv_text": cv, "jd_text": "Rust required."})
        for extra in [{"jd_text": ""}, {"jd_text": "Python", "requirements": []}, {"job_profile": "bad"}]:
            with self.assertRaises(ValueError):
                review_with_diagnostics(ReviewerStub(), {"cv_text": "Python", **extra})

    def test_max_requirements_retains_all_without_model_overflow(self):
        from jd_parser import SKILLS
        result, reviewer = self.review("\n".join(f"Knowledge of {skill}." for skill in list(SKILLS)[:21]))
        self.assertEqual(len(result["assessments"]), 21)
        self.assertIsNone(result["score"])
        self.assertEqual(reviewer.calls, [])


if __name__ == "__main__":
    unittest.main()
