"""Two-objective selection: minimize predicted QBER, maximize estimated output.

The nondominated front alone does not select a unique operating point. Explicit
selection modes keep that distinction visible in experiment logs.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Point:
    config: object
    qber: float
    rate: float
    delivered_bits: float


def front(points):
    """Exact pairwise nondominance; O(K^2) is adequate for the five settings.

    A dominates B if A has no larger error and no smaller delivered output,
    and is strictly better in at least one objective. Equal points are retained.
    """
    points = list(points)
    if any(not all(isfinite(v) for v in (p.qber,p.rate,p.delivered_bits)) or
           not 0 <= p.qber <= .5 or p.rate < 0 or p.delivered_bits < 0 for p in points):
        raise ValueError('Invalid Pareto objective values')
    return [p for p in points if not any(
        q.qber <= p.qber and q.delivered_bits >= p.delivered_bits and
        (q.qber < p.qber or q.delivered_bits > p.delivered_bits) for q in points)]


def select(scores, current, horizon=8, mode='delivered', scenario='low_skr',
           settling_cost=.25, improvement_margin=.01, qber_cap=.11):
    """Select only from a feasible Pareto front, with a reproducible tie rule.

    equivalent: preserve the old 90%-rate epsilon rule after front pruning.
    delivered: maximize expected delivered bits after switching cost, with
    lower QBER as the secondary objective. Both use predicted, not measured,
    candidate values; the controller separately checks analytical improvement.
    """
    if mode not in ('equivalent','delivered') or not 0 <= settling_cost < 1 or horizon < 0:
        raise ValueError('Invalid Pareto selection settings')
    if not 0 <= improvement_margin < 1 or not 0 < qber_cap < .5:
        raise ValueError('Invalid Pareto constraints')
    points = []
    for cfg,qber,rate in scores:
        if not all(isfinite(v) for v in (qber,rate)):
            raise ValueError('Nonfinite prediction')
        if 0 <= qber <= qber_cap and rate > 0:
            effective = horizon if mode=='equivalent' or cfg==current else max(0,horizon-settling_cost)
            points.append(Point(cfg,float(qber),float(rate),float(rate*effective)))
    nondominated = front(points)
    chosen = None
    if nondominated:
        if mode=='equivalent' and scenario=='high_qber':
            floor = .9*max(p.rate for p in nondominated)
            chosen = min((p for p in nondominated if p.rate >= floor),
                         key=lambda p:(p.qber,-p.rate,p.config!=current,p.config.name))
        else:
            chosen = min(nondominated,key=lambda p:(-p.delivered_bits,p.qber,p.config!=current,p.config.name))
    if mode=='delivered':
        previous = next((p for p in points if p.config==current),None)
        if horizon < 2 or chosen is None or (previous and
                chosen.delivered_bits <= previous.delivered_bits*(1+improvement_margin)):
            chosen = None
    audit = dict(mode=mode,horizon=horizon,settling_cost=settling_cost,
        objectives='minimize predicted QBER; maximize predicted accepted bits over horizon',
        selected=chosen.config.name if chosen else None,
        feasible_count=len(points),front_count=len(nondominated),
        candidates=[dict(config=p.config.name,qber=p.qber,rate=p.rate,
                         delivered_bits=p.delivered_bits,on_front=p in nondominated) for p in points])
    return chosen.config if chosen else None,audit
