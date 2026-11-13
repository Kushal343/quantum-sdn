from math import sqrt
import pytest
from qkd_sdn.simulation import BinomialEngine
from qkd_sdn.quantum import BB84Engine


@pytest.mark.parametrize('noise,fraction', [(0,0), (.015,.12), (.1,.7), (0,1)])
def test_count_sampler_and_aer_agree_with_bb84_distribution(noise, fraction):
    p = noise+fraction/4*(1-2*noise)
    results = [engine.measure(100000, noise, fraction)
               for engine in (BinomialEngine(91), BB84Engine(91))]
    for result in results:
        n = result['sifted']
        assert abs(n-50000) < 6*sqrt(25000)
        assert abs(result['errors']-n*p) <= 6*sqrt(n*p*(1-p))+1


def test_count_sampler_zero_detections():
    assert BinomialEngine(0).measure(0, .1)['sifted'] == 0
