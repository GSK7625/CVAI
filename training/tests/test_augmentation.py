"""Protect the development-only merge and pre-test validation selection."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "annotation"))
sys.path.insert(0, str(ROOT / "lightweight_cv"))
from prepare_augmented import contiguous_evidence, merge_sample
from train_augmented import choose
from build_round import content_hash


class AugmentationTests(unittest.TestCase):
    def test_span_hull_preserves_both_overlapping_contracts_in_original_order(self):
        text = "Contract B 2021-03 to 2022-01\nContract A 2021-01 to 2021-11"
        spans = [text.splitlines()[1], text.splitlines()[0]]
        self.assertEqual(contiguous_evidence(text, spans), text)
        with self.assertRaises(ValueError): contiguous_evidence(text, ["invented"])

    def test_unresolved_and_human_disagreement_are_not_silently_used_for_training(self):
        sample = {"sample_id":"s", "cv_group":"c", "jd_group":"j", "cv_text":"Used Python in paid work.",
                  "requirements":[{"id":f"r{i}","text":"Use Python", "weight":1} for i in range(1,4)]}
        ref = {"input_sha256":content_hash(sample), "assessments":[
            {"id":"r1","label":"met","evidence":[sample['cv_text']]},
            {"id":"r2","label":"needs_review","evidence":[]},
            {"id":"r3","label":"met","evidence":[sample['cv_text']]}]}
        human = {('s','r1'):{"label":"met","evidence":[sample['cv_text']]},
                 ('s','r3'):{"label":"not_evidenced","evidence":[]}}
        merged, sources, excluded = merge_sample(sample,ref,human)
        self.assertEqual([r['id'] for r in merged['requirements']], ['r1'])
        self.assertEqual(sources[0]['source'], 'human_first_pass_agrees_rule')
        self.assertEqual(len(excluded),2)
        self.assertEqual(sample['requirements'][2]['id'],'r3')

    def test_test_metric_cannot_affect_selection_and_old_validation_guard_is_applied(self):
        def row(name,old,new,test):
            return {'name':name,'old_validation':{'macro_f1':old,'score_mae':10},
                    'new_validation':{'macro_f1':new},'selection_score':(old+new)/2,'test_f1':test}
        baseline=row('baseline',.60,.40,.99)
        unsafe=row('unsafe',.50,.99,.99)
        safe=row('safe',.59,.80,.01)
        self.assertEqual(choose([baseline,unsafe,safe],.60)['name'],'safe')
        self.assertEqual(choose([baseline,unsafe],.60)['name'],'baseline')


if __name__ == '__main__': unittest.main()
