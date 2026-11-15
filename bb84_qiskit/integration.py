"""Explicit dependency boundaries for future measurement and controller adapters."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Protocol

from qkd_monitor.calibration import calibrate
from qkd_monitor.monitor import Monitor, POLICIES
from qkd_monitor.scenarios import simulate

try:
    from .bridge import sift_counts
except ImportError:
    from bridge import sift_counts


class DecisionProcessor(Protocol):
    def process(self, observation) -> dict:
        """Consume one ordered observation and return its monitoring decision."""


def default_policy_factory(config, calibration, policy) -> DecisionProcessor:
    return Monitor(config, calibration, policy)


def discard_decision(decision):
    """Default sink performs no external actions."""


@dataclass(frozen=True)
class Integration:
    """Supply compatible callables when embedding the runner in another system.

    Calibration and runtime share one count adapter. An alternative source must
    supply calibration covering the configured contexts and runtime observations
    paired with evaluator labels. For live observations without labels, use
    run_policy directly. Input/output contracts are documented in EXTENDING.md.
    """

    name: str = "optical-qiskit-v1"
    backend_label: str = "local StatevectorSampler"
    model_description: str = (
        "Python optical detection model plus Qiskit BB84 Y channel and sifting"
    )
    calibration_source: Callable = calibrate
    observation_source: Callable = simulate
    count_adapter: Callable = sift_counts
    policy_factory: Callable = default_policy_factory
    decision_sink: Callable = discard_decision
    policy_names: tuple[str, ...] = POLICIES


def run_policy(config, calibration, observations, policy,
               policy_factory=default_policy_factory, decision_sink=discard_decision):
    """Process an iterable, allowing a future transport adapter to observe decisions.

    The factory creates fresh state on each call. Sink failures propagate so a
    controller delivery error cannot be silently reported as successful.
    """
    processor = policy_factory(config, calibration, policy)
    decisions = []
    for observation in observations:
        decision = processor.process(observation)
        # Give observers a copy so external mutation cannot corrupt saved results.
        decision_sink(deepcopy(decision))
        decisions.append(decision)
    return decisions
