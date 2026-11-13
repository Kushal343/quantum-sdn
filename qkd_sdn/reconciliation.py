"""Fixed-length sparse syndrome reconciliation with min-sum decoding."""
import numpy as np


def graph(n, checks, seed=1729, degree=3):
    if not n > checks >= degree:
        raise ValueError('Invalid code dimensions')
    rng = np.random.default_rng(seed)
    return np.array([rng.choice(checks,degree,replace=False) for _ in range(n)])


def syndrome(key, edges, checks):
    return np.bincount(edges.ravel(), weights=np.repeat(key,edges.shape[1]), minlength=checks).astype(int)%2


def decode(bob, target, edges, checks, error_prior=.01, iterations=100):
    """Decode the error vector; no access to Alice's bits."""
    n, degree = edges.shape
    variables = np.repeat(np.arange(n),degree)
    rows = edges.ravel()
    groups = [np.flatnonzero(rows == j) for j in range(checks)]
    wanted = (syndrome(bob,edges,checks)+target)%2
    prior = np.log((1-error_prior)/error_prior)
    v = np.full(len(rows),prior)
    for iteration in range(iterations):
        c = np.zeros_like(v)
        for j, group in enumerate(groups):
            if not len(group): continue
            vals = v[group]; signs = np.where(vals < 0,-1.,1.)
            magnitude = np.abs(vals); order = np.argsort(magnitude)
            mins = np.full(len(group), magnitude[order[0]])
            mins[order[0]] = magnitude[order[1]] if len(group)>1 else 50.
            c[group] = .8*((-1)**wanted[j])*np.prod(signs)*signs*mins
        posterior = prior+np.bincount(variables,weights=c,minlength=n)
        errors = (posterior < 0).astype(int)
        candidate = (bob+errors)%2
        if np.array_equal(syndrome(candidate,edges,checks),target):
            return candidate,iteration+1
        v = np.clip(posterior[variables]-c,-50,50)
    return candidate,iterations
