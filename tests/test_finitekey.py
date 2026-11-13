import copy
import numpy as np
import pytest
from qkd_sdn.finitekey import key_budget
from qkd_sdn.reconciliation import graph,syndrome,decode
from distributed_demo import encode,verify


def test_budget_monotonicity_and_abort():
    a=key_budget(100000,50000,500,30000)
    assert a['length']>0
    assert key_budget(100000,50000,500,31000)['length']==a['length']-1000
    assert key_budget(100000,50000,500,30000,eps_sec=1e-12)['length']<a['length']
    assert key_budget(100000,50000,5000,30000)['length']==0
    with pytest.raises(ValueError):key_budget(10000,10000,10,100,source='decoy')


def test_decoder_corrects_errors_without_alice_input():
    rng=np.random.default_rng(1);a=rng.integers(0,2,1024);b=a.copy();b[[1,47,992]]^=1
    g=graph(1024,341)
    result,_=decode(b,syndrome(a,g,341),g,341)
    np.testing.assert_array_equal(result,a)


def test_authenticated_receiver_rejects_replay_and_tamper():
    secret=b'x'*32;p=encode(secret,'s','alice',0,'data',dict(value=1))
    assert verify(secret,'s','alice',0,p)['payload']['value']==1
    with pytest.raises(ValueError):verify(secret,'s','alice',1,p)
    bad=copy.deepcopy(p);bad[0]['payload']['value']=2
    with pytest.raises(ValueError):verify(secret,'s','alice',0,bad)
