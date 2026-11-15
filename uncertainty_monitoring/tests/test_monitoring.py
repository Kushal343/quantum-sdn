from dataclasses import asdict,replace
import json
from pathlib import Path
import tempfile
import unittest
from qkd_monitor.config import Config
from qkd_monitor.calibration import Calibration,calibrate
from qkd_monitor.scenarios import simulate
from qkd_monitor.monitor import Monitor,replay
from qkd_monitor.telemetry import Telemetry
from qkd_monitor.evaluation import run_metrics,paired_comparisons

ROOT=Path(__file__).resolve().parents[1]
TEST_TMP=ROOT/"tests"/".tmp"
TEST_TMP.mkdir(exist_ok=True)


def without_runtime(rows):
    return [{k:v for k,v in row.items() if k!="controller_microseconds"} for row in rows]


class MonitoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=Config.load(ROOT/"configs/default.json")
        cls.cal=calibrate(cls.cfg,42)

    def test_reproducible_calibration_and_full_budget(self):
        self.assertEqual(self.cal.to_dict(),calibrate(self.cfg,42).to_dict())
        self.assertAlmostEqual(self.cal.interval_alpha*len(self.cal.cells)*self.cfg.tests_per_window,self.cfg.calibration_failure_budget)
        self.assertAlmostEqual(self.cfg.alpha_test*self.cfg.windows*self.cfg.tests_per_window+self.cfg.calibration_failure_budget,self.cfg.alpha_run)

    def test_calibration_roundtrip_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(ROOT.resolve()))
            p=Path(tmp)/"cal.json";self.cal.save(p)
            self.assertEqual(Calibration.load(p,self.cfg).fingerprint,self.cal.fingerprint)
            data=json.loads(p.read_text());next(iter(data["cells"].values()))["0"]["lower"][0]=.99
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): Calibration.load(p,self.cfg)

    def test_calibration_wrong_configuration_rejected(self):
        with self.assertRaises(ValueError): Monitor(replace(self.cfg,config_version="other"),self.cal)

    def test_observable_schema_contains_no_hidden_truth(self):
        rows,_=simulate(self.cfg,"local_loss",42)
        fields=set(rows[0].to_dict())
        self.assertFalse(fields & {"event","target","attack","true_loss","scenario","extra_loss_db"})
        self.assertEqual(Telemetry.from_dict(rows[0].to_dict()),rows[0])

    def test_invalid_telemetry_rejected(self):
        row=simulate(self.cfg,"stable",42)[0][0]
        for bad in (replace(row,config_version="changed"),replace(row,errors=(10000000,0,0)),
                    replace(row,available=False),replace(row,classical_powers_mw=(float("nan"),1)),
                    replace(row,start_seconds=1),replace(row,emitted=(True,1,1))):
            with self.subTest(row=bad),self.assertRaises(ValueError): bad.validate(self.cfg)

    def test_duplicate_skipped_and_stale_rejected(self):
        rows,_=simulate(self.cfg,"stable",42)
        m=Monitor(self.cfg,self.cal);m.process(rows[0])
        with self.assertRaises(ValueError):m.process(rows[0])
        with self.assertRaises(ValueError):m.process(rows[self.cfg.channels*2])

    def test_fixed_configuration_preserved(self):
        rows,_=simulate(self.cfg,"local_background",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        self.assertEqual({row.config_version for row in rows},{self.cfg.config_version})
        self.assertTrue({d["action"] for d in out}<={"NONE","HOLD_OUTPUT","RESTORE_OUTPUT"})

    def test_stable_seed_has_no_quarantine(self):
        rows,_=simulate(self.cfg,"stable",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        self.assertFalse(any(d["held_next_window"] for d in out))

    def test_measured_power_change_is_explained(self):
        rows,_=simulate(self.cfg,"classical_power",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        event=[d for d in out if self.cfg.event_start<=d["window"]<self.cfg.event_end]
        self.assertTrue(all(d["category"]=="EXPLAINED_CHANGE" for d in event))
        self.assertFalse(any(d["held_next_window"] for d in out))

    def test_loss_detected_on_only_affected_channel_and_recovers(self):
        rows,_=simulate(self.cfg,"local_loss",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        holds=[d for d in out if d["action"]=="HOLD_OUTPUT"]
        self.assertEqual(len(holds),1);self.assertEqual(holds[0]["wavelength"],2)
        self.assertEqual(holds[0]["window"],self.cfg.event_start+self.cfg.anomaly_persistence-1)
        self.assertFalse(holds[0]["held_during_window"])
        self.assertTrue(holds[0]["held_next_window"])
        restores=[d for d in out if d["action"]=="RESTORE_OUTPUT"]
        self.assertEqual(len(restores),1)
        self.assertEqual(restores[0]["window"],self.cfg.event_end+self.cfg.recovery_windows-1)
        self.assertTrue(restores[0]["held_during_window"])

    def test_fault_and_tap_cannot_be_attributed(self):
        a,ta=simulate(self.cfg,"local_loss",42);b,tb=simulate(self.cfg,"passive_tap",42)
        self.assertEqual(a,b);self.assertNotEqual(ta,tb)
        self.assertEqual(without_runtime(replay(self.cfg,self.cal,a,"uncertainty")),without_runtime(replay(self.cfg,self.cal,b,"uncertainty")))

    def test_off_grid_is_inconclusive_not_attack(self):
        rows,_=simulate(self.cfg,"off_grid",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        event=[d for d in out if self.cfg.event_start<=d["window"]<self.cfg.event_end]
        self.assertTrue(all(d["category"]=="INCONCLUSIVE" for d in event))
        self.assertFalse(any(d["action"]=="HOLD_OUTPUT" for d in event))

    def test_context_pointwise_ablation_uses_same_features(self):
        rows,_=simulate(self.cfg,"classical_power",42)
        out=replay(self.cfg,self.cal,rows,"pointwise")
        self.assertEqual(len(out[0]["pvalues"]),6)
        self.assertEqual(out[0]["alpha_per_test"],self.cfg.alpha_run/self.cfg.tests_per_window)
        self.assertGreater(out[0]["alpha_per_test"],self.cfg.alpha_test)
        self.assertTrue(any(d["category"]=="EXPLAINED_CHANGE" for d in out))

    def test_gap_does_not_count_as_recovery(self):
        rows,_=simulate(self.cfg,"telemetry_gap",42)
        m=Monitor(self.cfg,self.cal)
        for row in rows:
            if row.window==self.cfg.event_start and row.wavelength==2:
                m.states[2].held=True;m.states[2].good_streak=2
            d=m.process(row)
            if not row.available:
                self.assertEqual(d["category"],"INCONCLUSIVE")
                self.assertTrue(d["held_next_window"])
                self.assertEqual(m.states[2].good_streak,0)

    def test_zero_detections_still_inform_gain(self):
        row=simulate(self.cfg,"stable",42)[0][0]
        empty=replace(row,detections=(0,0,0),errors=(0,0,0))
        out=Monitor(self.cfg,self.cal).process(empty)
        self.assertEqual(out["category"],"UNEXPLAINED_ANOMALY")
        self.assertIsNone(out["signal_qber"])

    def test_horizon_is_not_silently_restarted(self):
        rows,_=simulate(self.cfg,"stable",42)
        m=Monitor(self.cfg,self.cal)
        for row in rows: m.process(row)
        row=replace(rows[0],window=self.cfg.windows,start_seconds=self.cfg.windows*self.cfg.window_seconds,end_seconds=(self.cfg.windows+1)*self.cfg.window_seconds)
        self.assertEqual(m.process(row)["category"],"OUT_OF_BUDGET")

    def test_short_transient_does_not_trigger_hold(self):
        rows,_=simulate(self.cfg,"transient",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        self.assertTrue(any(d["anomalous"] for d in out))
        self.assertFalse(any(d["action"]=="HOLD_OUTPUT" for d in out))

    def test_metrics_use_event_end_decision_timing(self):
        rows,truth=simulate(self.cfg,"local_loss",42)
        out=replay(self.cfg,self.cal,rows,"uncertainty")
        metrics=run_metrics(self.cfg,"local_loss",42,"uncertainty",out,truth)
        self.assertEqual(metrics["detected_events"],1)
        self.assertEqual(metrics["mean_detection_delay_seconds"],2*self.cfg.window_seconds)
        self.assertGreater(metrics["benign_channel_windows_held"],0)
        self.assertEqual(metrics["false_hold_actions"],0)

    def test_paired_differences_have_correct_direction(self):
        rows=[{"scenario":"stable","seed":s,"policy":p,"false_hold_actions":v,"benign_channel_windows_held":v,"signal_detection_fraction_while_held":v/10} for s in (1,2,3) for p,v in (("uncertainty",0),("fixed_threshold",1))]
        result=paired_comparisons(rows)
        self.assertTrue(all(r["mean"]<0 for r in result))


if __name__=="__main__":unittest.main()
