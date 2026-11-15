"""Exact binomial intervals and conservative tests against composite rate intervals."""
from functools import lru_cache
from math import isfinite
from scipy.stats import beta, binom


@lru_cache(maxsize=131072)
def clopper_pearson(k: int, n: int, alpha: float = 0.05):
    if type(k) is not int or type(n) is not int or n < 1 or not 0 <= k <= n or not 0 < alpha < 1:
        raise ValueError("Require integer 0 <= k <= n, n>0, 0<alpha<1")
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def interval_pvalue(k, n, lower, upper):
    """p=min(1,2*min(P_lower[X<=k],P_upper[X>=k])).

    If the true rate lies in [lower,upper], either tail crossing alpha/2
    has probability <= alpha/2. Valid for sparse/zero counts without a
    normal approximation. No independence across features is required.
    """
    if n < 1 or not 0 <= k <= n or not all(isfinite(x) for x in (lower, upper)) or not 0 <= lower <= upper <= 1:
        raise ValueError("Invalid count or probability interval")
    low_tail = float(binom.cdf(k, n, lower))
    high_tail = float(binom.sf(k - 1, n, upper))
    return min(1.0, 2.0 * min(low_tail, high_tail))


def wilson(k, n, z=1.959963984540054):
    """Descriptive 95% interval; not used as an alarm/security threshold."""
    if n == 0:
        return None, None
    if not 0 <= k <= n:
        raise ValueError("Invalid counts")
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*((p*(1-p)/n + z*z/(4*n*n))**0.5)/d
    return max(0.0, c-h), min(1.0, c+h)
