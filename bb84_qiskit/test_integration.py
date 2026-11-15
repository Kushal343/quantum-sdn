"""Checks for extension boundaries and compatibility with saved observations."""
import json
from pathlib import Path
import unittest

from monitor import Config, Calibration, replay
from integration import run_policy
from qkd_monitor.telemetry import Telemetry


class IntegrationTests(unittest.TestCase):
    def test_sink_and_stream_match_existing_replay(self):
        folder = Path(__file__).parent / "results" / "connected_background"
        cfg = Config.load(folder / "config.json")
        calibration = Calibration.load(folder / "calibration.json", cfg)
        observations = [Telemetry.from_dict(json.loads(line))
                        for line in (folder / "telemetry.jsonl").read_text().splitlines()]
        expected = replay(cfg, calibration, observations, "uncertainty")
        sink_actions = []

        def sink(decision):
            sink_actions.append(decision["action"])
            decision["pvalues"].clear()

        actual = run_policy(cfg, calibration, iter(observations), "uncertainty",
                            decision_sink=sink)
        for old, new in zip(expected, actual, strict=True):
            old.pop("controller_microseconds")
            new.pop("controller_microseconds")
            self.assertEqual(old, new)
        self.assertEqual(len(sink_actions), len(observations))
        self.assertIn("HOLD_OUTPUT", sink_actions)

    def test_custom_factory_and_failed_delivery(self):
        class Processor:
            def process(self, value):
                return {"value": value}

        factory = lambda cfg, cal, policy: Processor()
        self.assertEqual(run_policy(None, None, iter([1, 2]), "custom",
                                    policy_factory=factory),
                         [{"value": 1}, {"value": 2}])

        def failed_sink(decision):
            raise ConnectionError("Endpoint unavailable")

        with self.assertRaises(ConnectionError):
            run_policy(None, None, iter([1]), "custom",
                       policy_factory=factory, decision_sink=failed_sink)


if __name__ == "__main__":
    unittest.main()
