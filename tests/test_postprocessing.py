import copy
import numpy as np
import pytest
from scipy.stats import hypergeom
from qkd_sdn.postprocessing import remaining_error_bound, toeplitz, Transcript, process


def test_sampling_bound_has_exact_coverage_for_all_error_populations():
    N, sample, alpha = 40, 10, .05
    for K in range(N+1):
        failure = 0
        for k in range(max(0,K-(N-sample)), min(sample,K)+1):
            upper = remaining_error_bound(N,sample,k,alpha)
            if (K-k)/(N-sample) > upper+1e-12:
                failure += hypergeom.pmf(k,N,K,sample)
        assert failure <= alpha+1e-12


def test_toeplitz_matches_explicit_matrix():
    x = np.array([1,0,1,1])
    seed = np.array([1,0,0,1,1,0])
    matrix = np.array([[seed[i+len(x)-1-j] for j in range(len(x))] for i in range(3)])
    np.testing.assert_array_equal(toeplitz(x,seed,3),matrix@x % 2)


def test_authentication_rejects_tampering_replay_and_reordering():
    t = Transcript(b'x'*32, 'session1')
    t.append('a', dict(value=1)); t.append('b', dict(value=2))
    assert t.verify(t.messages)
    altered = copy.deepcopy(t.messages); altered[0]['payload']['value'] = 3
    assert not t.verify(altered)
    assert not t.verify(t.messages[::-1])
    assert not Transcript(b'x'*32,'session2').verify(t.messages)
    assert not t.verify(t.messages[:-1])


def test_reconciliation_and_privacy_output_with_explicit_entropy():
    rng = np.random.default_rng(4)
    alice = rng.integers(0,2,2048); bob = alice.copy(); bob[101] ^= 1
    t = Transcript(b'x'*32,'test')
    result,a,b = process(alice,bob,t,rng,min_entropy_bits=1800)
    assert result['verified'] and result['candidate_length'] > 0
    np.testing.assert_array_equal(a,b)
    assert len(a) <= 1800-result['parity_leakage_bits']-64-59


def test_unspecified_entropy_fails_closed():
    x = np.zeros(512,dtype=int)
    result,a,b = process(x,x,Transcript(b'x'*32,'test'),np.random.default_rng(5))
    assert result['status'] == 'insufficient_entropy' and not len(a) and not len(b)


def test_tampered_transcript_aborts_before_processing():
    t = Transcript(b'x'*32, 'test'); t.append('sample', dict(errors=0))
    t.messages[0]['payload']['errors'] = 1
    with pytest.raises(ValueError, match='authentication'):
        process(np.zeros(10),np.zeros(10),t,np.random.default_rng(0))


def test_unreconciled_block_is_rejected():
    x = np.zeros(256,dtype=int)
    result,a,b = process(x,1-x,Transcript(b'x'*32,'test'),np.random.default_rng(0),min_entropy_bits=256)
    assert not result['verified'] and result['status'] == 'verification_failed'
    assert not len(a) and not len(b)


@pytest.mark.parametrize('args', [(10,0,0), (10,10,0), (10,5,6)])
def test_invalid_sampling_inputs(args):
    with pytest.raises(ValueError): remaining_error_bound(*args)
