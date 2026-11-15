from types import SimpleNamespace
import pytest
from sdn.ryu_core import RyuFlowService, initial_flows


class Parser:
    def __getattr__(self, name):
        return lambda *args, **kwargs:dict(kind=name,args=args,**kwargs)


def datapath(i):
    return SimpleNamespace(id=i,ofproto_parser=Parser(),ofproto=SimpleNamespace(
        OFPIT_APPLY_ACTIONS=4,OFPFC_DELETE=3,OFPP_ANY=0xffffffff,
        OFPG_ANY=0xffffffff,OFPVID_NONE=0,OFPVID_PRESENT=0x1000))


def test_ryu_vlan_rules_and_default_drop():
    messages=initial_flows(datapath(1),{i:'active' for i in range(1,5)})
    assert len(messages)==10
    assert messages[1]['priority']==0 and messages[1]['instructions']==[]
    for i in range(4):
        incoming=messages[2+i*2];outgoing=messages[3+i*2]
        assert incoming['match']['in_port']==i+1
        assert incoming['match']['vlan_vid']==0
        assert outgoing['match']['vlan_vid']==0x1000 | (101+i)
        assert outgoing['match']['in_port']==10


def test_acknowledged_isolation_scopes_and_latches():
    calls=[]
    service=RyuFlowService({i:datapath(i) for i in (1,2)},lambda dp,msgs:calls.append((dp.id,msgs)))
    service.initialize();calls.clear()
    assert service.apply(3,'hold')=='held'
    assert len(calls)==2
    for _,messages in calls:
        assert messages[0]['match']['in_port']==3
        assert messages[1]['match']['vlan_vid']==0x1000 | 103
    assert service.apply(3,'continue')=='active'
    service.apply(3,'isolate');calls.clear()
    assert service.apply(3,'continue')=='isolated' and not calls
    assert all(service.states[i]=='active' for i in (1,2,4))


def test_failed_flow_transaction_requires_replay_keeps_quarantine_intent():
    service=RyuFlowService({i:datapath(i) for i in (1,2)},lambda dp,msgs:None)
    service.initialize()
    def fail(dp,msgs):raise RuntimeError('barrier timeout')
    service.transact=fail
    with pytest.raises(RuntimeError):service.apply(3,'isolate')
    assert not service.status()['ready']
    assert service.states[3]=='isolated'
    with pytest.raises(RuntimeError):service.apply(1,'continue')


def test_replay_installs_isolation_before_forwarding():
    calls=[]
    service=RyuFlowService({i:datapath(i) for i in (1,2)},lambda dp,msgs:calls.append(msgs))
    service.states[3]='isolated';service.initialize()
    assert calls[0][2]['priority']==1000
    service.datapaths.pop(2)
    with pytest.raises(RuntimeError):service.apply(3,'hold')
