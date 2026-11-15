"""Numerical bootstrap and exact local checkpoint-resume regression checks."""
import random,unittest
import numpy as np
import torch
from torch import nn
from cpu_common import RUN
from evaluate_cpu import sorted_auc_plan,identity_bootstrap_auc,json_ready_report
from train_cpu import atomic_checkpoint
from verification import summarize

class NumericalGuards(unittest.TestCase):
    def test_reject_all_roc_threshold_is_valid_strict_json(self):
        import json
        metrics=summarize(np.array([.1,.2,.8,.9]),np.array([1,1,0,0]))
        self.assertTrue(np.isposinf(metrics['tar_far_1e-3_threshold']))
        converted=json_ready_report({'metrics':metrics})
        self.assertIsNone(converted['metrics']['tar_far_1e-3_threshold'])
        self.assertIn('reject_all',converted['metrics']['tar_far_1e-3_threshold_rule'])
        json.dumps(converted,allow_nan=False)
        with self.assertRaises(ValueError):json.dumps(json_ready_report({'auc':float('nan')}),allow_nan=False)
    def test_perfect_roc_has_finite_approximate_eer_threshold(self):
        metrics=summarize(np.array([.9,.8,.2,.1]),np.array([1,1,0,0]))
        self.assertEqual(metrics['eer'],0)
        self.assertTrue(np.isfinite(metrics['eer_threshold']))
    def test_weighted_auc_handles_ties(self):
        scores=np.array([.8,.8,.1,.1]);labels=np.array([1,0,1,0])
        self.assertAlmostEqual(sorted_auc_plan(scores,labels)(np.ones(4)),.5)
        self.assertIsNone(sorted_auc_plan(scores,labels)(np.array([1,0,1,0])))
    def test_bootstrap_tracks_both_endpoints(self):
        rows=[{'probe_identity':a,'enroll_identity':b} for a,b in [('a','a'),('b','b'),('a','b'),('b','a')]]
        result=identity_bootstrap_auc(np.array([.9,.8,.2,.1]),np.array([1,1,0,0]),rows,reps=100)
        self.assertEqual(result['identities'],2)
        self.assertEqual(result['auc_ci_95'],[1.,1.])
        self.assertGreater(result['valid_replicates'],0)
    def test_constant_quality_gate_fold(self):
        torch.manual_seed(42)
        layer=nn.Linear(10,5);folded=nn.Linear(6,5);x=torch.randn(16,6);q=torch.tensor([1.,0.,0.,1.])
        with torch.no_grad():
            folded.weight.copy_(layer.weight[:,:6]);folded.bias.copy_(layer.bias+layer.weight[:,6:]@q)
        torch.testing.assert_close(layer(torch.cat([x,q.expand(16,4)],dim=1)),folded(x))
    def test_optimizer_and_all_rng_states_resume_identically(self):
        torch.manual_seed(7);np.random.seed(7);random.seed(7)
        model=nn.Sequential(nn.Linear(4,8),nn.Dropout(.2),nn.Linear(8,1))
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-3)
        def step(model,optimizer):
            x=torch.randn(5,4)*float(np.random.uniform(.8,1.2));y=torch.full((5,1),random.random())
            optimizer.zero_grad(set_to_none=True);loss=((model(x)-y)**2).mean();loss.backward();optimizer.step()
        step(model,optimizer);step(model,optimizer)
        out=RUN/'tests';out.mkdir(exist_ok=True)
        path=out/'resume_fixture.pt'
        atomic_checkpoint(path,{'model':model.state_dict(),'optimizer':optimizer.state_dict(),
            'torch':torch.get_rng_state(),'numpy':np.random.get_state(),'python':random.getstate()})
        step(model,optimizer);expected=[p.detach().clone() for p in model.parameters()]
        restored=nn.Sequential(nn.Linear(4,8),nn.Dropout(.2),nn.Linear(8,1))
        opt=torch.optim.AdamW(restored.parameters(),lr=1e-3)
        c=torch.load(path,weights_only=False);restored.load_state_dict(c['model']);opt.load_state_dict(c['optimizer'])
        torch.set_rng_state(c['torch']);np.random.set_state(c['numpy']);random.setstate(c['python'])
        step(restored,opt)
        for actual,wanted in zip(restored.parameters(),expected):torch.testing.assert_close(actual,wanted,rtol=0,atol=0)

if __name__=='__main__':unittest.main()
