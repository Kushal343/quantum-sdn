"""Aer BB84 followed by classical research postprocessing; no keys logged."""
import argparse
import json
import secrets
from pathlib import Path
import numpy as np
from qkd_sdn.bb84 import bb84
from qkd_sdn.postprocessing import Transcript, process, remaining_error_bound


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pulses', type=int, default=24000)
    p.add_argument('--noise', type=float, default=.005)
    p.add_argument('--eve', type=float, default=0)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--assumed-entropy-fraction', type=float, default=0,
                   help='Explicit unproven entropy assumption; default zero releases no candidate')
    p.add_argument('--out', type=Path, default=Path('results/postprocessing'))
    a = p.parse_args()
    if not 0 <= a.assumed_entropy_fraction <= 1:
        p.error('Entropy fraction must be in [0,1]')
    r = bb84(a.pulses, channel_noise=a.noise, eve_fraction=a.eve, seed=a.seed)
    summary = {k:r[k] for k in ('n_sent','n_sifted','n_sample','sample_errors','qber','aborted')}
    summary['scope'] = 'Simulation; candidate key conditional on unproven entropy assumption'
    if r['n_sifted'] > r['n_sample'] > 0:
        summary['remaining_bit_error_upper_99_9'] = remaining_error_bound(r['n_sifted'],r['n_sample'],r['sample_errors'])
    if not r['aborted'] and len(r['alice_key']):
        # Authentication secret is independent of deterministic experiment RNG.
        t = Transcript(secrets.token_bytes(32), secrets.token_hex(16))
        t.append('sample_result', summary.copy())
        result, alice, bob = process(r['alice_key'], r['bob_key'], t,
            np.random.default_rng(a.seed+1), min_entropy_bits=int(len(r['alice_key'])*a.assumed_entropy_fraction))
        summary.update(result, transcript_authenticated=t.verify(t.messages),
                       candidate_keys_match=bool(len(alice) and np.array_equal(alice,bob)),
                       authenticated_messages=len(t.messages))
    else:
        summary['status'] = 'bb84_aborted'
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
