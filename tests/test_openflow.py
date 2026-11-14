import subprocess
from types import SimpleNamespace
import pytest
from sdn.openflow import OpenFlowController,SWITCHES


def fake(*args,**kwargs):return SimpleNamespace(stdout='')


def test_initial_forwarding_is_channel_scoped():
    c=OpenFlowController(fake);c.initialize()
    adds=[a[-1] for a in c.commands if a[3]=='add-flow']
    assert len(adds)==18
    assert sum('priority=0,actions=drop' in f for f in adds)==2
    for i in range(1,5):
        assert sum(f'mod_vlan_vid:{100+i},output:10' in f for f in adds)==2
        assert sum(f'in_port=10,dl_vlan={100+i},actions=strip_vlan,output:{i}' in f for f in adds)==2
    assert all(a[:3]==['ovs-ofctl','-O','OpenFlow13'] for a in c.commands)


def test_hold_resume_and_latched_isolation():
    c=OpenFlowController(fake);c.initialize();c.commands.clear()
    assert c.apply(3,'hold')=='held'
    assert len(c.commands)==4
    assert all('priority=1000' in a[-1] for a in c.commands)
    assert all('in_port=3,' in a[-1] or 'dl_vlan=103,' in a[-1] for a in c.commands)
    assert c.states[1]==c.states[2]==c.states[4]=='active'
    assert c.apply(3,'continue')=='active'
    assert all(a[3]=='del-flows' for a in c.commands[-2:])
    c.apply(3,'isolate');count=len(c.commands)
    assert c.apply(3,'continue')=='isolated' and len(c.commands)==count


def test_invalid_action_cannot_reach_command_runner():
    c=OpenFlowController(fake);c.initialize();count=len(c.commands)
    with pytest.raises(ValueError):c.apply(99,'hold')
    with pytest.raises(ValueError):c.apply(1,'shell command')
    assert len(c.commands)==count


def test_command_failure_does_not_report_success():
    c=OpenFlowController(fake);c.initialize()
    def fail(*args,**kwargs):raise subprocess.CalledProcessError(1,args[0])
    c.runner=fail
    with pytest.raises(subprocess.CalledProcessError):c.apply(3,'isolate')
    assert c.states[3]=='active' # owner must abort/tear down; never claim acknowledged isolation


def test_idempotent_initialization_and_no_optical_retune_claim():
    c=OpenFlowController(fake);c.initialize();count=len(c.commands)
    assert c.apply(1,'retune')=='active' and len(c.commands)==count
    with pytest.raises(RuntimeError):c.initialize()
