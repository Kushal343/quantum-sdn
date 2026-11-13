"""Classical QKD research components; not a complete security proof."""
import hashlib
import hmac
import json
from math import log2, floor
import numpy as np
from scipy.stats import hypergeom


def remaining_error_bound(total, sampled, errors, alpha=.001):
    """Exact one-sided inversion for a uniform sample WITHOUT replacement.

    Bounds remaining bit errors, not phase errors or Eve's information.
    """
    if not 0 < sampled < total or not 0 <= errors <= sampled or not 0 < alpha < 1:
        raise ValueError('Require a nonempty sample and remainder, valid errors and alpha')
    low, high = errors, total-sampled+errors
    while low < high:
        middle = (low+high+1)//2
        if hypergeom.cdf(errors, total, middle, sampled) >= alpha:
            low = middle
        else:
            high = middle-1
    return (low-errors)/(total-sampled)


def bits(values):
    a = np.asarray(values)
    if a.ndim != 1 or not np.isin(a, [0, 1]).all():
        raise ValueError('Expected a one-dimensional binary array')
    return a.astype(np.int64)


def toeplitz(key, seed, length):
    """Public-seed universal binary Toeplitz hash (also used for verification)."""
    key, seed = bits(key), bits(seed)
    if length < 0 or not len(key) or len(seed) != len(key)+length-1:
        raise ValueError('Invalid Toeplitz dimensions')
    if length == 0:
        return np.array([], dtype=np.int64)
    return np.correlate(seed, key[::-1], mode='valid') % 2


class Transcript:
    """In-process authenticated ordered transcript with session binding.

    HMAC-SHA256 is computational authentication using a pre-shared secret.
    This is not information-theoretic authentication or a network transport.
    """
    def __init__(self, secret, session):
        if len(secret) < 32 or not session:
            raise ValueError('Require a >=32-byte pre-shared secret and session identifier')
        self.secret, self.session, self.messages = secret, session, []

    def append(self, kind, payload):
        message = dict(session=self.session, sequence=len(self.messages), kind=kind, payload=payload)
        body = json.dumps(message, sort_keys=True, separators=(',', ':')).encode()
        message['tag'] = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        self.messages.append(message)

    def verify(self, messages):
        for i, item in enumerate(messages):
            message = dict(item)
            tag = message.pop('tag', '')
            if message.get('sequence') != i or message.get('session') != self.session:
                return False
            body = json.dumps(message, sort_keys=True, separators=(',', ':')).encode()
            if not hmac.compare_digest(tag, hmac.new(self.secret, body, hashlib.sha256).hexdigest()):
                return False
        return len(messages) == len(self.messages)


def reconcile(alice, bob, transcript, rng, passes=6):
    """Interactive parity/bisection demonstration, not full Cascade.

    Uncorrected even-error patterns are caught by independent verification.
    Every Alice parity disclosed is charged as one leakage bit.
    """
    alice, bob = bits(alice), bits(bob).copy()
    if len(alice) != len(bob) or not len(alice) or passes < 1:
        raise ValueError('Require equal nonempty keys and positive passes')
    leakage = 0

    def mismatch(indices):
        nonlocal leakage
        parity = int(alice[indices].sum() % 2)
        transcript.append('parity', dict(indices=indices.tolist(), parity=parity))
        leakage += 1
        return parity != int(bob[indices].sum() % 2)

    for turn in range(passes):
        order = rng.permutation(len(alice))
        width = min(8*2**turn, len(alice))
        for start in range(0, len(order), width):
            block = order[start:start+width]
            if mismatch(block):
                while len(block) > 1:
                    half = len(block)//2
                    block = block[:half] if mismatch(block[:half]) else block[half:]
                bob[block[0]] ^= 1
    return bob, leakage


def process(alice, bob, transcript, rng, min_entropy_bits=0, epsilon_pa=1e-9, verify_bits=64):
    """Return candidate keys only under an explicit pre-transcript entropy assumption.

    Caller must justify H_min^epsilon(A|E) for the supplied raw block, accounting
    for parameter estimation and earlier disclosure. Default zero fails closed.
    """
    alice, bob = bits(alice), bits(bob)
    if not transcript.verify(transcript.messages):
        raise ValueError('Transcript authentication failed')
    if not 0 <= min_entropy_bits <= len(alice) or not 0 < epsilon_pa < 1 or verify_bits < 1:
        raise ValueError('Invalid security parameters')
    corrected, leakage = reconcile(alice, bob, transcript, rng)
    seed = rng.integers(0, 2, len(alice)+verify_bits-1)
    tag = toeplitz(alice, seed, verify_bits)
    transcript.append('verification', dict(seed=seed.tolist(), tag=tag.tolist()))
    if not transcript.verify(transcript.messages):
        raise ValueError('Transcript authentication failed')
    verified = bool(np.array_equal(tag, toeplitz(corrected, seed, verify_bits)))
    length = max(0, floor(min_entropy_bits-leakage-verify_bits-2*log2(1/epsilon_pa)))
    result = dict(verified=verified, parity_leakage_bits=leakage,
                  verification_leakage_bits=verify_bits, assumed_min_entropy_bits=min_entropy_bits,
                  candidate_length=0, status='verification_failed' if not verified else 'insufficient_entropy')
    if not verified or not length:
        return result, np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    seed = rng.integers(0, 2, len(alice)+length-1)
    transcript.append('privacy_seed', dict(seed=seed.tolist(), length=length))
    if not transcript.verify(transcript.messages):
        raise ValueError('Transcript authentication failed')
    result.update(candidate_length=length, status='candidate_under_assumed_entropy')
    return result, toeplitz(alice, seed, length), toeplitz(corrected, seed, length)
