import copy
import pytest
from qkd_sdn.authentication import OneUseAuthenticator,authentication_budget,polynomial,MAX_BYTES
from qkd_sdn.asymmetric import prepare


def test_one_use_authentication_and_key_exhaustion():
    key=OneUseAuthenticator.new_key()
    a=OneUseAuthenticator(key,'s','alice');b=OneUseAuthenticator(key,'s','alice')
    packet=a.sign('test',dict(bits=[0,1,0]))
    assert b.receive(packet)['kind']=='test'
    with pytest.raises(ValueError):a.sign('test',{})
    with pytest.raises(ValueError):b.receive(packet)


def test_tamper_burns_verification_attempt():
    key=OneUseAuthenticator.new_key();a=OneUseAuthenticator(key,'s','alice');b=OneUseAuthenticator(key,'s','alice')
    packet=a.sign('test',dict(value=1));bad=copy.deepcopy(packet);bad[0]['payload']['value']=2
    with pytest.raises(ValueError):b.receive(bad)
    with pytest.raises(ValueError):b.receive(packet)


def test_auth_budget_and_message_cap():
    assert authentication_budget(6)['authentication_secret_bits']==1524
    assert 0<authentication_budget(6)['authentication_failure_bound']<1e-30
    with pytest.raises(ValueError):polynomial(b'x'*(MAX_BYTES+1),4)


def test_aer_basis_separation_and_ideal_agreement():
    import numpy as np
    r=prepare(100,80,seed=1,noise=0)
    a,b=r['alice'],r['bob'];ab=np.array(a['bases']);bb=np.array(b['bases']);d=np.array(b['detected'],dtype=bool)
    keep=d&(ab==bb)
    assert (keep&(ab==0)).sum()>=100 and (keep&(ab==1)).sum()>=80
    np.testing.assert_array_equal(np.array(a['bits'])[keep],np.array(b['bits'])[keep])
