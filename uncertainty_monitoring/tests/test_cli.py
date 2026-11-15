import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
TEST_TMP=ROOT/"tests"/".tmp"
TEST_TMP.mkdir(exist_ok=True)


class CLITests(unittest.TestCase):
    def test_demo_and_observable_only_replay(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(ROOT.resolve()))
            out=Path(tmp)/"demo"
            cmd=[sys.executable,"-m","qkd_monitor","demo","--scenario","local_loss","--out",str(out)]
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            for name in ("report.html","manifest.json","telemetry.jsonl","truth_evaluation_only.jsonl","summary.json","paired_comparisons.json","run_metrics.csv"):
                self.assertTrue((out/name).is_file(),name)
            replay_path=Path(tmp)/"replay.jsonl"
            p=subprocess.run([sys.executable,"-m","qkd_monitor","replay","--telemetry",str(out/"telemetry.jsonl"),"--calibration",str(out/"calibration/seed_42.json"),"--out",str(replay_path)],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            def normalized(path):
                return [{k:v for k,v in json.loads(line).items() if k!="controller_microseconds"} for line in path.read_text().splitlines()]
            self.assertEqual(normalized(out/"decisions_uncertainty.jsonl"),normalized(replay_path))
            html=(out/"report.html").read_text()
            self.assertIn("data:image/png;base64,",html)
            self.assertIn("No finite-key security engine",html)

    def test_invalid_seed_count_fails_cleanly(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(ROOT.resolve()))
            p=subprocess.run([sys.executable,"-m","qkd_monitor","benchmark","--seeds","0","--out",tmp],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertIn("positive seed count",p.stderr)


if __name__=="__main__":unittest.main()
