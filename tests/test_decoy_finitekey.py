from math import exp
import numpy as np
import pytest
from qkd_sdn.decoy_finitekey import budget
from qkd_sdn.physics import Channel,gain_error
from decoy_finite_demo import counts


def test_small_samples_fail_closed_and_large_block_can_produce_bound():
    small=counts(100000,0)
    assert budget(*small,sum(small[0])//3+1)['length']==0
    large=counts(1000000000,0)
    base=budget(*large,sum(large[0])//3+1)
    assert base['length']>0 and base['phase_upper']<.11
    more_leak=budget(*large,sum(large[0])//3+1001)
    assert more_leak['length']==base['length']-1000
    stricter=budget(*large,sum(large[0])//3+1,eps_sec=1e-12)
    assert stricter['length']<=base['length']


def test_interception_and_empty_counts_abort():
    large=counts(1000000000,0,intercept=.8)
    assert budget(*large,sum(large[0])//3+1)['length']==0
    assert budget([0]*3,[0]*3,[0]*3,0)['length']==0


def test_bounds_against_latent_photon_number_counts():
    # Independent generative check: explicit 0/1/multiphoton populations.
    # Latent counts are never provided to the estimator.
    ch=Channel();probs=[.75,.2,.05]
    for seed in range(30):
        rng=np.random.default_rng(seed)
        nx=[];true0=true1=0
        emitted=rng.multinomial(1000000000,probs)
        for mu,n in zip([.6,.12,0],emitted):
            p0=exp(-mu);p1=mu*p0;p2=max(0,1-p0-p1)
            populations=rng.multinomial(n,[p0,p1,p2])
            gain,_=gain_error(mu,ch)
            y0=ch.background;y1=ch.eta+(1-ch.eta)*ch.background
            y2=(gain-p0*y0-p1*y1)/p2 if p2 else 0
            detected=[int(rng.binomial(int(pop),float(np.clip(y,0,1)))) for pop,y in zip(populations,[y0,y1,y2])]
            nx.append(sum(detected));true0+=detected[0];true1+=detected[1]
        result=budget(nx,nx,[max(1,int(n*.02)) for n in nx],0)
        assert result['vacuum_lower']<=true0
        assert result['single_x_lower']<=true1


@pytest.mark.parametrize('kwargs', [dict(probabilities=(.75,.2,0)),dict(intensities=(.1,.2,0)),dict(eps_sec=0),dict(leak_ec=-1)])
def test_invalid_parameters_rejected(kwargs):
    args=dict(nx=[100,20,1],nz=[100,20,1],mz=[1,0,0],leak_ec=30);args.update(kwargs)
    with pytest.raises(ValueError):budget(**args)


def test_noninteger_and_impossible_counts_rejected():
    with pytest.raises(ValueError):budget([1.5,2,3],[1,2,3],[0,0,0],0)
    with pytest.raises(ValueError):budget([1,2,3],[1,2,3],[2,0,0],0)
