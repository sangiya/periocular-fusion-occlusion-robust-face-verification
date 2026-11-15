"""Checks for tied-score thresholds, dyadic bootstrap, and frozen inputs."""
import csv,json,sys,unittest
import numpy as np
from cpu_common import HERE,EXPERIMENT,RUN,calibrate,at_threshold,sha

class ResearchGuards(unittest.TestCase):
    def test_threshold_uses_no_test_scores_and_rejects_boundary_ties(self):
        scores=np.array([.9,.8,.8,.2,.1]);labels=np.array([1,0,0,0,0])
        threshold=calibrate(scores,labels,.25)
        self.assertGreater(threshold,.8)
        self.assertEqual(at_threshold(scores,labels,threshold)['false_accepts'],0)
        test=np.array([.95,.94,.93,.9,.1])
        self.assertEqual(threshold,calibrate(scores,labels,.25))
        self.assertGreater(at_threshold(test,labels,threshold)['far'],.25)
    def test_zero_false_accept_threshold_is_strict(self):
        scores=np.array([.9,.8,.2,.1]);labels=np.array([1,0,0,0])
        threshold=calibrate(scores,labels,0)
        self.assertEqual(at_threshold(scores,labels,threshold)['false_accepts'],0)
    def test_invalid_calibration_is_rejected(self):
        with self.assertRaises(ValueError):calibrate([np.nan,.2],[0,1],.01)
        with self.assertRaises(ValueError):calibrate([.3],[1],.01)
    def test_frozen_protocol_hashes(self):
        plan=json.loads((EXPERIMENT/'EXPERIMENT_PLAN.json').read_text())
        for name,digest in plan['input_hashes'].items():self.assertEqual(sha(EXPERIMENT/name),digest,name)
    def test_confirmed_near_duplicate_is_absent(self):
        with (EXPERIMENT/'training_manifest.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
        names={r['face_path'] for r in rows}
        self.assertNotIn('data/ROF/images/neutral/harrison_ford/000011.jpg',names)
        self.assertNotIn('data/ROF/images/neutral/mark_hamill/000002.jpg',names)
        self.assertEqual(len(rows),6171)
    def test_no_training_endpoint_in_validation_or_test(self):
        with (EXPERIMENT/'training_manifest.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
        train={r['face_path'] for r in rows if r['split']=='train'}
        for p in EXPERIMENT.glob('*_pairs.csv'):
            with p.open(encoding='utf-8') as f:pairs=list(csv.DictReader(f))
            for r in pairs:
                self.assertNotIn(r['probe_face_path'],train);self.assertNotIn(r['enroll_face_path'],train)

if __name__=='__main__':unittest.main()
