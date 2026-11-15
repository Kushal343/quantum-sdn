"""Regression checks for the BB84-to-monitor count contract."""

from dataclasses import replace
from pathlib import Path
import unittest

from monitor import Config, qiskit_calibration, qiskit_trace, replay, sift_counts


class ConnectionTests(unittest.TestCase):
    def test_audit_reconstructs_monitor_counts(self):
        detected, errors, audit = sift_counts((10000, 3000, 1000),
                                              (5000, 1000, 100), (200, 40, 50), 42)
        for category in range(3):
            pairs = audit["basis_counts"][category]
            self.assertEqual(sum(p["detections"] for p in pairs.values()),
                             audit["optical_detections"][category])
            self.assertEqual(detected[category],
                             pairs["ZZ"]["detections"] + pairs["XX"]["detections"])
            self.assertEqual(errors[category],
                             pairs["ZZ"]["disagreements"] + pairs["XX"]["disagreements"])
            self.assertLessEqual(errors[category], detected[category])

    def test_reproducible_and_zero_counts(self):
        args = ((10000, 3000, 1000), (5000, 1000, 100), (200, 40, 50), 42)
        self.assertEqual(sift_counts(*args), sift_counts(*args))
        detected, errors, audit = sift_counts((0, 0, 0), (0, 0, 0), (0, 0, 0), 42)
        self.assertEqual(detected, (0, 0, 0))
        self.assertEqual(errors, (0, 0, 0))
        self.assertEqual(audit["circuit_results"], [])

    def test_loss_is_detected_with_qiskit_calibration(self):
        cfg = Config.load(Path(__file__).with_name("monitor_config.json"))
        cfg = replace(cfg, wavelengths_nm=(cfg.wavelengths_nm[0],),
                      background_coupling_per_mw=(cfg.background_coupling_per_mw[0],),
                      classical_power_grid_mw=(1.0,), windows=20,
                      event_start=5, event_end=12)
        cfg.validate()
        calibration, _ = qiskit_calibration(cfg, 42)
        rows, _, _ = qiskit_trace(cfg, "local_loss", 42)
        decisions = replay(cfg, calibration, rows, "uncertainty")
        holds = [d for d in decisions if d["action"] == "HOLD_OUTPUT"]
        restores = [d for d in decisions if d["action"] == "RESTORE_OUTPUT"]
        self.assertEqual([d["window"] for d in holds], [6])
        self.assertEqual([d["window"] for d in restores], [14])
        self.assertEqual({row.config_version for row in rows}, {"qiskit-sifted-v1"})


if __name__ == "__main__":
    unittest.main()
