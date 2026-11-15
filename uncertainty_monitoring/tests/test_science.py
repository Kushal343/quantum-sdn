"""Scientific properties and exact small-sample coverage checks."""
from dataclasses import replace
from pathlib import Path
import unittest
import numpy as np
from scipy.stats import binom
from qkd_monitor.config import Config
from qkd_monitor.physics import probabilities,sample_counts
from qkd_monitor.statistics import clopper_pearson,interval_pvalue,wilson

ROOT=Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg=Config.load(ROOT/"configs/default.json")

    def test_roundtrip_and_hash(self):
        self.assertEqual(self.cfg,Config.from_dict(self.cfg.to_dict()))
        self.assertEqual(len(self.cfg.fingerprint),64)
        self.assertNotEqual(self.cfg.fingerprint,replace(self.cfg,windows=121).fingerprint)

    def test_invalid_parameters_fail(self):
        for key,value in (("alpha_run",.001),("pulses_per_window",True),("detector_efficiency",2),
                          ("intensities",[.1,.5,0]),("intensity_probabilities",[.8,.1,.05]),
                          ("fibre_length_km",float("nan")),("event_end",130)):
            data=self.cfg.to_dict();data[key]=value
            with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):
                Config.from_dict(data)


class StatisticsTests(unittest.TestCase):
    def test_interval_boundaries(self):
        self.assertEqual(clopper_pearson(0,10)[0],0)
        self.assertEqual(clopper_pearson(10,10)[1],1)
        self.assertGreater(clopper_pearson(0,10)[1],0)
        self.assertLess(clopper_pearson(10,10)[0],1)

    def test_exact_interval_coverage_enumerated(self):
        n=25;alpha=.05
        intervals=[clopper_pearson(k,n,alpha) for k in range(n+1)]
        for p in np.linspace(.001,.999,61):
            coverage=sum(binom.pmf(k,n,p) for k,(lo,hi) in enumerate(intervals) if lo<=p<=hi)
            self.assertGreaterEqual(coverage,1-alpha-1e-12)

    def test_composite_test_size_enumerated(self):
        n=40;lo=.15;hi=.30;alpha=.05
        rejected=[k for k in range(n+1) if interval_pvalue(k,n,lo,hi)<=alpha]
        for p in np.linspace(lo,hi,31):
            size=sum(binom.pmf(k,n,p) for k in rejected)
            self.assertLessEqual(size,alpha+1e-12)

    def test_interval_uncertainty_can_only_reduce_rejection(self):
        for k in range(41):
            self.assertGreaterEqual(interval_pvalue(k,40,.1,.4),interval_pvalue(k,40,.2,.3))

    def test_zero_sample_handling(self):
        self.assertEqual(wilson(0,0),(None,None))
        with self.assertRaises(ValueError): clopper_pearson(0,0)

    def test_descriptive_example(self):
        lo,hi=wilson(520,10000)
        self.assertAlmostEqual((hi-lo)*50,.435,delta=.005)


class PhysicsTests(unittest.TestCase):
    def setUp(self):
        self.cfg=Config.load(ROOT/"configs/default.json")

    def test_probabilities_are_physical_in_extreme_conditions(self):
        for loss in (0,3,1000):
            for bg in (0,.001,10):
                q,t=probabilities(self.cfg,2,(4,4),loss,bg)
                self.assertTrue(np.all((0<=t)&(t<=q)&(q<=1)))

    def test_loss_reduces_gain(self):
        q,_=probabilities(self.cfg,0,(1,1))
        q_loss,_=probabilities(self.cfg,0,(1,1),3)
        self.assertLess(q_loss[0],q[0]);self.assertEqual(q_loss[2],q[2])

    def test_classical_power_changes_wavelengths_differently(self):
        changes=[]
        for wavelength in range(self.cfg.channels):
            low,_=probabilities(self.cfg,wavelength,(1,1))
            high,_=probabilities(self.cfg,wavelength,(4,4))
            changes.append(high[0]-low[0])
        self.assertTrue(all(v>0 for v in changes))
        self.assertGreater(max(changes)-min(changes),.0001)

    def test_vacuum_background_errors_are_random(self):
        q,t=probabilities(self.cfg,0,(1,1))
        self.assertAlmostEqual(t[2]/q[2],.5)

    def test_no_background_vacuum_is_empty(self):
        cfg=replace(self.cfg,dark_probability_per_gate=0)
        q,t=probabilities(cfg,0,(0,0))
        self.assertEqual(q[2],0);self.assertEqual(t[2],0)

    def test_sampling_counts_and_reproducibility(self):
        a=sample_counts(self.cfg,0,(1,1),100000,np.random.default_rng(42))
        b=sample_counts(self.cfg,0,(1,1),100000,np.random.default_rng(42))
        self.assertEqual(a,b);self.assertEqual(sum(a[0]),100000)
        for n,d,e in zip(*a): self.assertTrue(0<=e<=d<=n)

    def test_sampling_mean_matches_model(self):
        q,t=probabilities(self.cfg,0,(1,1))
        rng=np.random.default_rng(89);totals=np.zeros((3,3))
        for _ in range(150):
            totals+=np.array(sample_counts(self.cfg,0,(1,1),100000,rng))
        for j in range(3):
            n,d,e=totals[:,j]
            self.assertLess(abs(d-n*q[j]),6*np.sqrt(n*q[j]*(1-q[j]))+1)
            self.assertLess(abs(e-n*t[j]),6*np.sqrt(n*t[j]*(1-t[j]))+1)


if __name__=="__main__": unittest.main()
