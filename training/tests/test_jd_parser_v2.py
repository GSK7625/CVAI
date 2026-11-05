import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from jd_parser_v2 import prepare_jd, logic_skills


ML_JD = """Data Cleaning: Clean and preprocess tabular records using pandas to ensure data accuracy and consistency for downstream reporting.
Batch Data Processing: Transform large-scale batch records using Apache Spark to support analytical data pipelines.
Database Querying: Write and optimize SQL queries to extract, filter, and aggregate records for the water quality dashboard.
Machine Learning Development: Train and evaluate classification baseline models using scikit-learn.
Industry Experience: Around 4 months of paid professional experience as a Data or ML Engineer.
Core Technical Stack: Demonstrated professional experience working with pandas (cleaning tabular records), Apache Spark (transforming batch records), and SQL (querying and aggregating records).
Machine Learning: Hands-on capability with scikit-learn to train classification baseline models (self-directed project or build experience is fully accepted).
Workflow Orchestration: Prior experience with Airflow is not required for this position."""


class ParserTests(unittest.TestCase):
    def test_real_ml_jd_has_five_deduplicated_criteria(self):
        p = prepare_jd(ML_JD, "Machine Learning Engineer")
        self.assertEqual(p["unresolved"], [])
        self.assertEqual(p["status"], "ready")
        items = {c["subject"]: c for c in p["criteria"]}
        self.assertEqual(set(items), {"pandas", "Apache Spark", "SQL", "scikit-learn", "data/ML engineer"})
        for name in ["pandas", "Apache Spark", "SQL"]:
            self.assertEqual(items[name]["level"], "professional")
            self.assertEqual(len(items[name]["sources"]), 2)
        self.assertEqual(items["scikit-learn"]["level"], "practical")
        self.assertEqual(items["data/ML engineer"]["duration"], {"relation": "approximate", "months": 4})
        self.assertEqual(p["ignored"][0]["reason"], "explicitly_not_required")
        for item in p["criteria"] + [{"sources": p["ignored"]}]:
            for source in item["sources"]:
                self.assertEqual(p["source_text"][source["start"]:source["end"]], source["text"])

    def test_vietnamese_prose_priority_and_negation(self):
        p = prepare_jd("Yêu cầu bắt buộc:\nBiết Python và SQL.\nƯu tiên:\nCó dự án với PyTorch.\nKhông yêu cầu Airflow.")
        self.assertEqual(p["status"], "ready")
        items = {c["subject"]: c for c in p["criteria"]}
        self.assertEqual(items["Python"]["weight"], 3)
        self.assertEqual(items["SQL"]["weight"], 3)
        self.assertEqual(items["PyTorch"]["weight"], 1)
        self.assertEqual(items["PyTorch"]["level"], "practical")
        self.assertNotIn("Airflow", items)

    def test_independent_clause_scope(self):
        p = prepare_jd("Python required, SQL preferred, Airflow not required.")
        self.assertEqual(p["status"], "ready")
        self.assertEqual({c["subject"]: c["weight"] for c in p["criteria"]}, {"Python": 3, "SQL": 1})

    def test_unknown_independent_condition_is_not_hidden_by_known_skill(self):
        p = prepare_jd("Python required and strong communication skills mandatory.")
        self.assertEqual(p["status"], "needs_review")
        self.assertIn("communication", p["unresolved"][0]["text"])

    def test_mixed_skill_levels_do_not_leak_between_clauses(self):
        p = prepare_jd("Basic knowledge of Python and professional experience with SQL.")
        self.assertEqual({c["subject"]: c["level"] for c in p["criteria"]}, {"Python": "basic", "SQL": "professional"})

    def test_shared_level_and_priority_apply_to_entire_list(self):
        p = prepare_jd("Basic knowledge of Python and SQL required.")
        self.assertEqual([(c["level"], c["weight"]) for c in p["criteria"]], [("basic", 3), ("basic", 3)])

    def test_prefix_negation_and_contract_duration(self):
        p = prepare_jd("Python required.\nNo prior experience with Airflow is required.")
        self.assertEqual([c["subject"] for c in p["criteria"]], ["Python"])
        p = prepare_jd("Contract length: 6 months.", "Machine Learning Engineer")
        self.assertEqual(p["criteria"], [])

    def test_deep_groups_require_review_without_crashing(self):
        p = prepare_jd("(" * 50 + "Python or Java" + ")" * 50)
        self.assertEqual(p["status"], "needs_review")

    def test_or_group_is_not_two_required_skills(self):
        for text in ["Python or Java required.", "Python hoặc Java bắt buộc.", "One of Python, Java required."]:
            with self.subTest(text=text):
                p = prepare_jd(text)
                self.assertEqual(p["status"], "ready")
                self.assertEqual(len(p["criteria"]), 1)
                self.assertEqual(p["criteria"][0]["logic"]["op"], "any")

    def test_parenthesized_alternatives(self):
        p = prepare_jd("Python and (SQL or PostgreSQL) required.")
        self.assertEqual(p["status"], "ready")
        self.assertEqual(len(p["criteria"]), 2)
        self.assertEqual(sorted(len(logic_skills(c["logic"])) for c in p["criteria"]), [1, 2])

    def test_duration_relations_are_preserved(self):
        cases = [("At least 2 years", {"relation": "minimum", "months": 24}),
                 ("2-3 years", {"relation": "range", "min_months": 24, "max_months": 36}),
                 ("1 year to 18 months", {"relation": "range", "min_months": 12, "max_months": 18}),
                 ("Khoảng 4 tháng", {"relation": "approximate", "months": 4}),
                 ("Up to 6 months", {"relation": "maximum", "months": 6}),
                 ("More than 2 years", {"relation": "more_than", "months": 24})]
        for prefix, expected in cases:
            with self.subTest(prefix=prefix):
                p = prepare_jd(prefix + " experience as a backend developer.")
                self.assertEqual(p["criteria"][0]["duration"], expected)

    def test_skill_duration_is_not_role_duration(self):
        p = prepare_jd("2 years of professional Python experience.")
        c = p["criteria"][0]
        self.assertEqual(c["kind"], "skill")
        self.assertEqual(c["constraints"][0]["kind"], "skill_duration")

    def test_html_sections_and_provenance(self):
        p = prepare_jd("<h3>Requirements</h3><ul><li>Python required</li><li>SQL preferred</li></ul><h3>Benefits</h3><p>Free Java courses</p><script>Rust required</script>")
        self.assertEqual(p["status"], "ready")
        self.assertEqual({c["subject"] for c in p["criteria"]}, {"Python", "SQL"})
        for item in p["criteria"]:
            for src in item["sources"]:
                self.assertEqual(p["source_text"][src["start"]:src["end"]], src["text"])

    def test_unknown_conditions_are_retained(self):
        for text in ["Python and Elixir required.", "Python or elixir required.", "Strong communication skills required."]:
            with self.subTest(text=text):
                self.assertEqual(prepare_jd(text)["status"], "needs_review")

    def test_qualifications_are_extracted_separately(self):
        p = prepare_jd("Bachelor's degree in Computer Science.\nEnglish IELTS 6.5 required.\nAWS certification preferred.")
        self.assertEqual(p["status"], "ready")
        self.assertEqual({c["kind"] for c in p["criteria"]}, {"education", "language", "certification"})

    def test_extra_constraints_are_not_silently_dropped(self):
        p = prepare_jd("Advanced Python 3.12 required.")
        self.assertEqual({c["kind"] for c in p["criteria"][0]["constraints"]}, {"proficiency", "version"})

    def test_duplicates_and_conflicts(self):
        self.assertEqual(len(prepare_jd("Python required.\nPython required.")["criteria"]), 1)
        self.assertIn("conflicting_priority", {i["code"] for i in prepare_jd("Python required.\nPython preferred.")["unresolved"]})

    def test_profiles_are_deterministic_and_validate_input(self):
        self.assertEqual(prepare_jd(ML_JD), prepare_jd(ML_JD))
        for text in [None, " ", "x" * 20001]:
            with self.assertRaises(ValueError):
                prepare_jd(text)


if __name__ == "__main__":
    unittest.main()
