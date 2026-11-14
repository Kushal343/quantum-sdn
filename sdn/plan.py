"""Cross-platform QKD -> OpenFlow dry-run; no switches or packets are created."""
import json
from pathlib import Path
from types import SimpleNamespace
from .openflow import OpenFlowController


def main():
    from qkd_sdn.simulation import NetworkSimulator,conditions
    from qkd_sdn.controller import Controller
    controller=OpenFlowController(runner=lambda *args,**kwargs:SimpleNamespace(stdout=''))
    controller.initialize();qkd=Controller();sim=NetworkSimulator(42,100000,engine='binomial');rows=[]
    for step in range(12):
        ts=[]
        for i in range(4):
            ch,eve,tap=conditions('intercept',step,wavelength=i)
            ts.append(sim.observe(ch,qkd.states[i]['config'],eve,tap))
        decisions=qkd.decide(ts)
        for i,d in enumerate(decisions):
            state=controller.apply(i+1,d['action'])
            rows.append(dict(interval=step,channel=f'lambda_{i+1}',action=d['action'],planned_forwarding=state))
    out=Path('results/sdn');out.mkdir(parents=True,exist_ok=True)
    (out/'plan.json').write_text(json.dumps(dict(scope='DRY RUN ONLY: commands not executed; no packet validation',
        rows=rows,commands=controller.commands),indent=2))
    print('Dry-run final channel states:',controller.states)
    print('Saved results/sdn/plan.json; no switches were contacted.')


if __name__=='__main__':main()
