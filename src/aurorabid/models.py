"""Named-feature probability models and explicit model metadata."""
from pathlib import Path
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from .features import FEATURE_COLUMNS, ordered_features


def probability_metrics(labels, probabilities):
    return {
        "auc": float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) > 1 else None,
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
        "brier": float(brier_score_loss(labels, probabilities)),
        "n": int(len(labels)),
    }


class ProbabilityModel:
    def __init__(self, kind="logistic", seed=42):
        if kind == "logistic":
            self.estimator = make_pipeline(StandardScaler(), LogisticRegression(C=.2, max_iter=1000, random_state=seed))
        elif kind == "boosted":
            self.estimator = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=7, l2_regularization=10, random_state=seed)
        else:
            raise ValueError(f"Unknown model: {kind}")
        self.kind = kind

    def fit(self, features, labels):
        if len(np.unique(labels)) < 2:
            raise ValueError("Training needs positive and negative labels.")
        self.estimator.fit(ordered_features(features), labels)
        return self

    def predict(self, features):
        return self.estimator.predict_proba(ordered_features(features))[:, 1]


def fit_models(train, validation):
    """Select by validation log loss; CVR means P(conversion | click, x)."""
    selected, metrics = {}, []
    for target, label in [("ctr", "clicked"), ("cvr", "converted")]:
        tr = train if target == "ctr" else train[train.clicked == 1]
        va = validation if target == "ctr" else validation[validation.clicked == 1]
        candidates = []
        for kind in ["logistic", "boosted"]:
            model = ProbabilityModel(kind).fit(tr, tr[label])
            score = probability_metrics(va[label], model.predict(va))
            metrics.append({"target": target, "model": kind, "split": "validation", **score})
            candidates.append((score["log_loss"], model))
        selected[target] = min(candidates, key=lambda pair: pair[0])[1]
    return selected, metrics


def save_models(models, directory, metadata):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump({"schema": list(FEATURE_COLUMNS), "models": models, "metadata": metadata}, directory / "probability_models.joblib")


def load_models(directory):
    path = Path(directory) / "probability_models.joblib"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run: aurorabid reproduce")
    bundle = joblib.load(path)
    if bundle["schema"] != list(FEATURE_COLUMNS):
        raise ValueError("Checkpoint feature schema does not match this code. Retrain.")
    return bundle
