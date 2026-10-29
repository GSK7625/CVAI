"""Small counterexamples for the label rubric and source parsing."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "build_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_dataset", SCRIPT)
dataset = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dataset
SPEC.loader.exec_module(dataset)


def candidate(facts=None, months=0, track="backend"):
    return {"track": track, "months": months, "experience_evidence": f"Paid experience: {months} months.",
            "facts": facts or {}, "has_role_detail": True}


class LabelTests(unittest.TestCase):
    def test_keyword_negation_does_not_establish_skill(self):
        cv = candidate({"Python": {"state": "negated", "evidence": "I have not used Python."}})
        for kind in ("basic", "practical", "professional"):
            self.assertEqual(dataset.assess(cv, {"kind": kind, "tech": "Python"}), ("not_evidenced", None))

    def test_similar_names_are_not_interchangeable(self):
        cv = candidate({"JavaScript": {"state": "project", "evidence": "Built a UI in JavaScript."},
                        "React Native": {"state": "paid", "evidence": "Used React Native in paid work."}})
        for tech in ("Java", "React"):
            self.assertEqual(dataset.assess(cv, {"kind": "practical", "tech": tech}), ("not_evidenced", None))

    def test_course_does_not_become_production_experience(self):
        cv = candidate({"Docker": {"state": "course", "evidence": "Completed guided Docker lessons."}})
        self.assertEqual(dataset.assess(cv, {"kind": "basic", "tech": "Docker"})[0], "met")
        self.assertEqual(dataset.assess(cv, {"kind": "practical", "tech": "Docker"})[0], "partial")
        self.assertEqual(dataset.assess(cv, {"kind": "professional", "tech": "Docker"})[0], "partial")

    def test_project_is_not_paid_work(self):
        cv = candidate({"Python": {"state": "project", "evidence": "Independent Python project."}})
        self.assertEqual(dataset.assess(cv, {"kind": "practical", "tech": "Python"})[0], "met")
        self.assertEqual(dataset.assess(cv, {"kind": "professional", "tech": "Python"})[0], "partial")

    def test_experience_threshold_and_role(self):
        requirement = {"kind": "experience", "track": "backend", "months": 12}
        self.assertEqual(dataset.assess(candidate(months=0), requirement), ("not_evidenced", None))
        self.assertEqual(dataset.assess(candidate(months=8), requirement)[0], "partial")
        self.assertEqual(dataset.assess(candidate(months=12), requirement)[0], "met")
        self.assertEqual(dataset.assess(candidate(months=24, track="qa"), requirement), ("not_evidenced", None))

    def test_rewrite_does_not_invent_achievements(self):
        cv = candidate({"Redis": {"state": "listed", "evidence": "Listed skill: Redis."}})
        issue = dataset.issues_for(cv)[0]
        self.assertIn("Nếu đã dùng Redis", issue["suggestion"])
        self.assertNotIn("10.000", issue["suggestion"])

    def test_parse_list_is_not_eval(self):
        self.assertEqual(dataset.parse_list("['Python', None]"), ["Python", None])
        with self.assertRaises((ValueError, SyntaxError)):
            dataset.parse_list("__import__('os').getcwd()")

    def test_sampling_band_respects_requirement_weights(self):
        pair = {"requirements": [{"id": "r1", "weight": 1}, {"id": "r2", "weight": 1},
                                 {"id": "r3", "weight": 1}, {"id": "r4", "weight": 3}],
                "target": {"assessments": [{"id": f"r{i}", "status": "met" if i < 4 else "not_evidenced"}
                                           for i in range(1, 5)]}}
        self.assertEqual(dataset.pair_band(pair), "middle")

    def test_direct_contacts_are_redacted(self):
        result = dataset.clean_source_text("mail person@example.com see https://example.com call +84 912 345 678")
        self.assertNotIn("person@example.com", result)
        self.assertNotIn("https://example.com", result)
        self.assertNotIn("912", result)

    def test_existing_annotations_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            protected = output / "train.jsonl"
            protected.write_text("reviewed data", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                dataset.build(output, output / "missing-source.csv")
            self.assertEqual(protected.read_text(encoding="utf-8"), "reviewed data")


if __name__ == "__main__":
    unittest.main()
