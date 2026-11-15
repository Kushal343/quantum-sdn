import json
from pathlib import Path
from experiments.protocol_demo import run

if __name__=='__main__':
    rows=[]
    for label,options in [('normal',{}),('tamper',dict(fault='tamper')),('intercept',dict(eve=.8))]:
        result=run(**options)
        if label=='normal':assert result['keys_match']
        else:assert not result['keys_match']
        rows.append(dict(case=label,result=result))
    out=Path('results/protocol');out.mkdir(parents=True,exist_ok=True)
    (out/'validation.json').write_text(json.dumps(rows,indent=2))
    (out/'summary.json').write_text(json.dumps(rows[0]['result'],indent=2))
    print('Normal agreement, tamper rejection and intercept abort passed')
