import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lightweight_cv"))
from evidence_features import KINDS, STATES
from retrieved_context import model_inputs


def features(cv, retrieved, **extra):
    req = {"id": "r", "text": "Paid professional experience with Java.", "weight": 2}
    sample = {"cv_text": cv, "requirements": [req], **extra}
    record = {"sample_id": "new-cv", "requirement_id": "r",
              "retrieved": [{"text": retrieved, "start": cv.index(retrieved)}]}
    return model_inputs([sample], np.zeros((1, 3)), [record])[0]


class RetrievedContextTests(unittest.TestCase):
    def test_same_bullet_in_two_sections(self):
        bullet = "Built Java tooling for the catalog."
        for section, expected in [("Experience", "paid"), ("Projects", "project")]:
            result = features(section + "\n" + bullet, bullet)
            self.assertEqual(result[3 + len(KINDS) + STATES.index(expected)], 1)

    def test_unretrieved_skills_and_gold_do_not_enter_model(self):
        bullet = "Worked on a JavaScript dashboard."
        base = features("Experience\n" + bullet, bullet)
        modified = features("Experience\nUsed Java during paid work.\n" + bullet, bullet,
                            target={"assessments": [{"id": "r", "status": "met"}]})
        np.testing.assert_array_equal(base, modified)
        self.assertEqual(base[3 + len(KINDS) + STATES.index("absent")], 1)

    def test_heading_does_not_override_explicit_negation_or_personal_project(self):
        for text, state in [("I have never used Java.", "negated"),
                            ("I used Java in a personal project.", "project")]:
            result = features("Experience\n" + text, text)
            self.assertEqual(result[3 + len(KINDS) + STATES.index(state)], 1)
            self.assertEqual(result[3 + len(KINDS) + STATES.index("paid")], 0)
