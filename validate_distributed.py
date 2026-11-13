"""Separate-process acceptance, decoding, parameter-abort and tamper checks."""
import json
from pathlib import Path
from distributed_demo import run


if __name__=='__main__':
    rows=[]
    for noise in [.001,.005,.02,.08]:
        for seed in range(3):
            result=run(noise=noise,seed=seed)
            rows.append(dict(noise=noise,seed=seed,result=result))
    tampered=run(fault='tamper')
    assert not tampered.get('keys_match',False)
    assert all(not p.get('accepted') for p in tampered.get('participants',{}).values())
    rows.append(dict(fault='tamper',result=tampered))
    out=Path('results/distributed');out.mkdir(parents=True,exist_ok=True)
    (out/'validation.json').write_text(json.dumps(rows,indent=2))
    print('Completed 12 channel trials and authenticated-tamper rejection')
