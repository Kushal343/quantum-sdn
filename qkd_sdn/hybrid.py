"""Calibrated monitoring from the branch plus the main branch's retuning loop."""
from .controller import Controller, select_configuration, candidate_scores, wilson
from .monitoring import count_features
from .physics import expected


class HybridController(Controller):
    def __init__(self, calibration, horizon, policy='hybrid', predictor=None,
                 alpha_run=.05, recovery_windows=3):
        if policy not in ('hybrid', 'uncertainty', 'pareto_front', 'pareto') or type(horizon) is not int or horizon < 1:
            raise ValueError('Invalid calibrated policy or horizon')
        if not 0 < calibration.calibration_budget < alpha_run < 1 or recovery_windows < 1:
            raise ValueError('Invalid alarm/recovery budget')
        super().__init__('adaptive', predictor)
        self.policy, self.calibration, self.horizon = policy, calibration, horizon
        self.alpha_run, self.recovery_windows = alpha_run, recovery_windows
        self.alpha_test = (alpha_run-calibration.calibration_budget)/(horizon*4*6)
        self.window = 0
        for state in self.states.values():
            state.update(held=False, good=0, version=0)

    def decide(self, telemetry):
        if len(telemetry) != 4:
            raise ValueError('Exactly four ordered wavelength records are required')
        decisions = []
        for i, t in enumerate(telemetry):
            s = self.states[i]
            s['selection_audit'] = None
            action, category, reason = 'continue', 'NORMAL', 'Counts fit independent calibration'
            pvalues, flagged = {}, []
            lo, hi = 0.0, 1.0
            if s['isolated']:
                action, category, reason = 'isolated', 'QUARANTINED', 'Latched isolation; diagnostic acquisition only'
            else:
                try:
                    count_features(t)
                    sig = t['records']['signal']
                    lo, hi = wilson(sig['errors'], sig['sifted'])
                    valid = (t.get('available', True) and sig['sifted'] >= 100 and
                             all(t['records'][label]['emitted'] > 0 for label in ('signal','decoy','vacuum')) and
                             t['config'] == s['config'] and t.get('window', self.window) == self.window)
                    if self.window >= self.horizon:
                        category, reason = 'OUT_OF_BUDGET', 'Declared monitoring horizon exhausted'
                    elif not valid:
                        category, reason = 'INCONCLUSIVE', 'Missing, sparse, stale, or wrong-configuration telemetry'
                    else:
                        assessed = self.calibration.assess(t, self.alpha_test)
                        if assessed is None:
                            category, reason = 'INCONCLUSIVE', 'Context outside finite calibration grid'
                        else:
                            pvalues = assessed
                            flagged = [f for f, p in pvalues.items() if p <= self.alpha_test]
                except (KeyError, TypeError, ValueError):
                    category, reason = 'INCONCLUSIVE', 'Malformed count telemetry'
                if category in ('INCONCLUSIVE', 'OUT_OF_BUDGET'):
                    s['evidence'], s['good'], s['held'] = 0, 0, True
                    action = 'hold'
                elif flagged:
                    s['evidence'] += 1
                    s['good'], s['held'] = 0, True
                    category, reason = 'UNEXPLAINED_ANOMALY', ', '.join(flagged)
                    action = 'hold'
                    if s['evidence'] >= 2:
                        s['isolated'], s['pending'] = True, None
                        action = 'isolate'
                elif hi >= .11:
                    s['evidence'], s['good'], s['held'] = 0, 0, True
                    action, category, reason = 'hold', 'OPERATING_CAP', 'Error uncertainty reaches illustrative 11% cap'
                else:
                    s['evidence'] = 0
                    s['good'] += 1
                    if s['held'] and s['good'] < self.recovery_windows:
                        action, category, reason = 'hold', 'RECOVERING', 'Require three consecutive usable passing windows'
                    else:
                        s['held'] = False
                        if self.policy != 'uncertainty':
                            action, reason = self._adapt(s, t, lo)
                            if action != 'continue' or lo > .025:
                                category = 'EXPLAINED_DEGRADATION'
            decisions.append(dict(action=action, category=category, reason=reason,
                qber_low=lo, qber_high=hi, pvalues=pvalues, flagged_features=flagged,
                alpha_per_test=self.alpha_test, config_version=s['version'],
                selection_audit=s['selection_audit']))
        self.window += 1
        return decisions

    def _adapt(self, s, t, lower_qber):
        if s['pending']:
            trial = s['pending']
            trial['rates'].append(t['skr_estimate'])
            if len(trial['rates']) < 2:
                return 'verify', 'Collecting post-change observations'
            action = 'keep'
            if sum(trial['rates'])/len(trial['rates']) < .9*trial['before']:
                s['config'] = trial['old']
                s['version'] += 1
                action = 'rollback'
            s['pending'], s['cooldown'] = None, 4
            return action, 'Two-window estimated-rate trial completed; 10% rollback tolerance'
        if s['cooldown']:
            s['cooldown'] -= 1
            return 'continue', 'Retuning cooldown'
        gain = t['records']['signal']['gain']
        if s['baseline_gain'] is None:
            s['baseline_gain'] = gain
        if gain >= .75*s['baseline_gain'] and lower_qber <= .025:
            return 'continue', 'Within calibrated expectations'
        scenario='high_qber' if lower_qber > .025 else 'low_skr'
        horizon=8
        if self.policy in ('pareto_front','pareto'):
            from .pareto import select
            from .monitoring import context_key
            scores=[score for score in candidate_scores(t['channel'],t['clock_hz'],self.predictor)
                    if context_key(t['channel'],score[0]) in self.calibration.cells]
            if self.policy=='pareto':
                horizon=min(8,max(0,self.horizon-self.window-1))
            candidate,s['selection_audit']=select(scores,t['config'],horizon,
                'delivered' if self.policy=='pareto' else 'equivalent',scenario)
        else:
            candidate = select_configuration(t['channel'],t['clock_hz'],scenario,self.predictor)
        if candidate is not None and candidate != t['config']:
            # Candidate must be independently calibrated before it can be tried.
            from .monitoring import context_key
            if context_key(t['channel'], candidate) not in self.calibration.cells:
                return 'continue', 'Candidate has no independent calibration'
            old_e, old_r = expected(t['config'], t['channel'], t['clock_hz'])
            new_e, new_r = expected(candidate, t['channel'], t['clock_hz'])
            # Charge 25% of one interval, amortized over an eight-interval horizon.
            if new_e <= .11 and new_r*(horizon-.25) > old_r*horizon*1.01:
                s['pending'] = dict(old=t['config'], before=t['skr_estimate'], rates=[])
                s['config'], s['version'] = candidate, s['version']+1
                return 'retune', 'Calibrated candidate passes analytical benefit and settling-cost checks'
        return 'continue', 'Explained degradation; no worthwhile calibrated change'
