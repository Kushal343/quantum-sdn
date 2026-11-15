"""One policy factory for the command line, experiments and live Mininet lab."""
POLICIES = ('fixed','aggregate','per_wavelength','adaptive','uncertainty','hybrid','pareto_front','pareto')


def make_controller(policy, horizon, predictor=None, calibration=None):
    if policy not in POLICIES:
        raise ValueError('Unknown policy')
    if policy in ('hybrid','uncertainty','pareto_front','pareto'):
        from .hybrid import HybridController
        from .monitoring import calibrate
        from .noise import known_contexts
        calibration = calibration or calibrate(known_contexts())
        return HybridController(calibration, horizon, policy, predictor)
    from .controller import Controller
    return Controller(policy, predictor)
