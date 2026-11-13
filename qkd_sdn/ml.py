"""Optional surrogate, trained on analytical model outputs, not measured data.

All candidate settings for a channel remain in the same train/test split.
"""
from dataclasses import asdict
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from .physics import Channel, CANDIDATES, expected


def features(ch, cfg):
    return [ch.eta, ch.background, ch.misalignment, cfg.mu, cfg.nu,
            cfg.p_signal, cfg.p_decoy]


class Predictor:
    def __init__(self, model):
        self.model = model

    def predict(self, ch, cfg, clock):
        qber, fraction = self.model.predict([features(ch, cfg)])[0]
        return float(np.clip(qber, 0, 0.5)), float(max(0, fraction)*clock)


def train(seed=7, conditions=400):
    if conditions < 20:
        raise ValueError("Need at least 20 channel conditions")
    rng = np.random.default_rng(seed)
    order = rng.permutation(conditions)
    test_ids = set(order[:max(1, conditions//5)])
    xtrain, ytrain, xtest, ytest = [], [], [], []
    held = []
    for i in range(conditions):
        ch = Channel(distance_km=float(rng.uniform(10, 60)),
                     extra_loss_db=float(rng.uniform(0, 6)),
                     traffic=float(rng.uniform(0, 8)),
                     misalignment=float(rng.uniform(0.005, 0.04)))
        if i in test_ids:
            held.append(ch)
        for c in CANDIDATES:
            q, r = expected(c, ch, 1)
            xs, ys = (xtest, ytest) if i in test_ids else (xtrain, ytrain)
            xs.append(features(ch, c)); ys.append([q, r])
    # Separate targets to avoid their different scales dominating one forest.
    from sklearn.multioutput import MultiOutputRegressor
    model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100,
                min_samples_leaf=2, random_state=seed, n_jobs=1)).fit(xtrain, ytrain)
    prediction = model.predict(xtest)
    errors = mean_absolute_error(ytest, prediction, multioutput="raw_values")
    predictor = Predictor(model)
    regrets = []
    for ch in held:
        true = [expected(c, ch, 1)[1] for c in CANDIDATES]
        picked = max(range(len(CANDIDATES)), key=lambda j: predictor.predict(ch, CANDIDATES[j], 1)[1])
        if max(true) > 0:
            regrets.append((max(true)-true[picked])/max(true))
    metrics = {"training_source": "analytical asymptotic teacher, not Qiskit shot labels",
               "split": "held-out channel conditions, all candidates grouped",
               "train_conditions": conditions-len(test_ids), "test_conditions": len(test_ids),
               "qber_mae": float(errors[0]), "secret_fraction_mae": float(errors[1]),
               "mean_relative_candidate_regret": float(np.mean(regrets)) if regrets else 0.0}
    return predictor, metrics
