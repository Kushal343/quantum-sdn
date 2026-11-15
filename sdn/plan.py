"""Cross-platform QKD -> OpenFlow dry-run; no switches or packets are created."""
import json
from pathlib import Path
from types import SimpleNamespace
from .openflow import OpenFlowController


def main():
    from qkd_sdn.simulation import NetworkSimulator
    from qkd_sdn.noise import Scenario
    from qkd_sdn.policies import make_controller
    controller=OpenFlowController(runner=lambda *args,**kwargs:SimpleNamespace(stdout=''))
    controller.initialize();qkd=make_controller('hybrid',12)
    sim=NetworkSimulator(42,100000,engine='binomial');rows=[]
    disturbance=Scenario('intercept',42)
    for step in range(12):
        ts=[]
        for i in range(4):
            ts.append(disturbance.observe(sim,qkd.states[i]['config'],step,i))
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
