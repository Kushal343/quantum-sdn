"""Equation (2), arXiv:1103.4130v2, ideal single-photon asymmetric BB84.

This calculator is NOT applicable to the existing weak-coherent decoy telemetry.
Qtol and the reconciliation communication cap must be fixed before observing data.
"""
from math import sqrt, log, log2, floor, ceil
from .physics import entropy


def key_budget(n, k, test_errors, leak_cap, qtol=.02, eps_sec=1e-9,
               eps_cor=1e-12, preparation_quality=1., source='single_photon'):
    if source != 'single_photon':
        raise ValueError('This theorem does not cover coherent-pulse decoy telemetry')
    if (not isinstance(n,int) or not isinstance(k,int) or n <= 0 or k <= 0
            or not 0 <= test_errors <= k or not 0 <= leak_cap
            or not 0 <= qtol < .5 or not 0 < eps_sec < 1
            or not 0 < eps_cor < 1 or not 0 < preparation_quality <= 1):
        raise ValueError('Invalid finite-key parameters')
    mu = sqrt((n+k)/(n*k)*(k+1)/k*log(4/eps_sec))
    phase = min(.5, qtol+mu)
    entropy_term = max(0., n*(preparation_quality-entropy(phase)))
    penalty = 1+2*log2(1/eps_sec)+log2(1/eps_cor)
    length = max(0, floor(entropy_term-leak_cap-penalty))
    abort = test_errors/k > qtol
    return dict(protocol='ideal_single_photon_asymmetric_bb84', n=n, k=k,
                test_errors=test_errors, qtol=qtol, mu=mu, phase_bound=phase,
                entropy_term_bits=entropy_term, reconciliation_cap_bits=leak_cap,
                verification_bits=ceil(log2(1/eps_cor)), extraction_penalty_bits=penalty,
                epsilon_secrecy=eps_sec, epsilon_correctness=eps_cor,
                epsilon_qkd=eps_sec+eps_cor,
                authentication='separate computational HMAC assumption',
                length=0 if abort else length, parameter_abort=abort)
