"""Run from project root: sudo <venv>/bin/python -m sdn.lab --mode selftest."""
import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from .openflow import OpenFlowController


def preflight():
    if platform.system()!='Linux' or os.geteuid()!=0:
        raise RuntimeError('Live Mininet requires Linux and root. See sdn/README.md.')
    for tool in ('ovs-ofctl','ovs-vsctl','ip','ping'):
        if not shutil.which(tool):raise RuntimeError(f'Missing executable: {tool}')
    import mininet.net
    from .openflow import SWITCHES
    for switch in SWITCHES:
        result=subprocess.run(['ovs-vsctl','br-exists',switch],capture_output=True,timeout=10)
        if result.returncode==0:raise RuntimeError(f'Bridge {switch} already exists; refusing to replace it')
        if result.returncode!=2:raise RuntimeError('Open vSwitch service is unavailable')


def selftest(net,c):
    from .topology import connectivity
    report={}
    report['initial']=connectivity(net)
    assert all(report['initial'].values()),'Initial forwarding failed'
    # Different subnets are intentional; use a direct Ethernet neighbor to test separation.
    a,b=net.get('a1','b2')
    a.cmd('ip route add 10.2.0.2/32 dev a1-eth0')
    a.cmd('ip neigh replace 10.2.0.2 lladdr 02:00:00:00:02:02 nud permanent dev a1-eth0')
    b.cmd('ip route add 10.1.0.1/32 dev b2-eth0')
    b.cmd('ip neigh replace 10.1.0.1 lladdr 02:00:00:00:01:01 nud permanent dev b2-eth0')
    _,_,code=a.pexec(['ping','-n','-c','1','-W','1',b.IP()])
    assert code!=0,'Cross-channel leakage'
    report['cross_channel_blocked']=True
    c.apply(3,'hold');report['held']=connectivity(net)
    assert report['held']==dict(lambda_1=True,lambda_2=True,lambda_3=False,lambda_4=True)
    c.apply(3,'continue');report['resumed']=connectivity(net)
    assert all(report['resumed'].values())
    c.apply(3,'isolate');c.apply(3,'continue');report['isolated']=connectivity(net)
    assert report['isolated']==report['held'],'Isolation did not remain latched'
    report['flows']=c.snapshot()
    return report


def monitor(net,c,args):
    import time
    from qkd_sdn.simulation import NetworkSimulator,conditions
    from qkd_sdn.controller import Controller
    from .topology import connectivity
    sim=NetworkSimulator(args.seed,args.pulses,engine=args.engine);qkd=Controller()
    rows=[]
    for step in range(args.steps):
        telemetry=[]
        for i in range(4):
            ch,eve,tap=conditions(args.scenario,step,wavelength=i)
            telemetry.append(sim.observe(ch,qkd.states[i]['config'],eve,tap))
        decisions=qkd.decide(telemetry)
        for i,d in enumerate(decisions):c.apply(i+1,d['action'])
        probes=connectivity(net)
        if args.verify:
            for i in range(4):
                assert probes[f'lambda_{i+1}']==(c.states[i+1]=='active'),f'Flow/packet mismatch on channel {i+1}'
        for i,(t,d) in enumerate(zip(telemetry,decisions)):
            row=dict(interval=step,channel=f'lambda_{i+1}',qber=t['qber'],action=d['action'],
                     forwarding=c.states[i+1],ping_ok=probes[f'lambda_{i+1}'])
            rows.append(row);print(json.dumps(row),flush=True)
        time.sleep(args.interval)
    return dict(rows=rows,flows=c.snapshot(),engine=args.engine,
        scope='QKD telemetry is simulated; ICMP probes traverse actual Mininet namespaces and OVS flows')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['selftest','monitor','cli'],default='selftest')
    p.add_argument('--scenario',choices=['normal','intercept','weak_intercept','loss','noise','tap','shared_noise'],default='intercept')
    p.add_argument('--engine',choices=['aer','binomial'],default='binomial')
    p.add_argument('--steps',type=int,default=12);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--pulses',type=int,default=100000);p.add_argument('--interval',type=float,default=0)
    p.add_argument('--out',type=Path,default=Path('results/sdn'))
    p.add_argument('--verify',action='store_true',help='Assert measured packet reachability matches installed policy')
    args=p.parse_args()
    if args.steps<1 or args.pulses<1000 or args.interval<0:p.error('Invalid experiment settings')
    preflight()
    from .topology import create_network
    net=create_network();c=OpenFlowController()
    try:
        c.initialize()
        if args.mode=='selftest':report=selftest(net,c)
        elif args.mode=='monitor':report=monitor(net,c,args)
        else:
            from mininet.cli import CLI
            CLI(net);report=dict(flows=c.snapshot())
        args.out.mkdir(parents=True,exist_ok=True)
        (args.out/f'{args.mode}.json').write_text(json.dumps(report,indent=2))
        print(f'Saved {args.out.resolve()}')
    finally:net.stop()


if __name__=='__main__':main()
