"""
Inference wrapper around the trained model artifact.

This is the only module the rest of the app should import from `ml` for
predictions -- it hides joblib/sklearn details behind a single function that
takes a plain list of symptom strings and returns a plain dict, so the
Streamlit pages and the chatbot don't need to know anything about feature
vectors or model internals.
"""
import os

import joblib
import pandas as pd

from config import MODEL_PATH
from ml.symptom_data import ALL_SYMPTOMS, EMERGENCY_SYMPTOMS

_artifact = None


def _load():
    global _artifact
    if _artifact is None:
        if not os.path.exists(MODEL_PATH):
            from ml.train_model import train
            train()
        _artifact = joblib.load(MODEL_PATH)
    return _artifact


def predict(symptoms: list[str]) -> dict:
    """
    Args:
        symptoms: list of symptom strings (must match ALL_SYMPTOMS vocabulary;
                   unrecognised strings are silently ignored).

    Returns a dict with:
        department            - top predicted department
        department_confidence - probability of the top department (0-1)
        top_departments       - list of (department, probability) for top 3
        urgency                - predicted urgency level
        urgency_confidence     - probability of that urgency level
        is_emergency_override  - True if a known emergency symptom was present
                                  (in which case urgency is forced to "Emergency"
                                  regardless of what the classifier says -- we
                                  never want a model's uncertainty to downgrade
                                  a red-flag symptom)
    """
    artifact = _load()
    dept_clf = artifact["department_clf"]
    urg_clf = artifact["urgency_clf"]
    feature_names = artifact["feature_names"]

    known = set(symptoms) & set(ALL_SYMPTOMS)
    if not known:
        return {
            "department": None,
            "department_confidence": 0.0,
            "top_departments": [],
            "urgency": None,
            "urgency_confidence": 0.0,
            "is_emergency_override": False,
            "error": "No recognised symptoms were provided.",
        }

    row = pd.DataFrame([[int(f in known) for f in feature_names]], columns=feature_names)

    dept_probs = dept_clf.predict_proba(row)[0]
    dept_classes = dept_clf.classes_
    dept_ranking = sorted(zip(dept_classes, dept_probs), key=lambda x: -x[1])

    is_emergency = bool(known & EMERGENCY_SYMPTOMS)
    if is_emergency:
        urgency = "Emergency"
        urgency_conf = 1.0
    else:
        urg_probs = urg_clf.predict_proba(row)[0]
        urg_classes = urg_clf.classes_
        best_idx = urg_probs.argmax()
        urgency = urg_classes[best_idx]
        urgency_conf = float(urg_probs[best_idx])

    return {
        "department": dept_ranking[0][0],
        "department_confidence": float(dept_ranking[0][1]),
        "top_departments": [(d, float(p)) for d, p in dept_ranking[:3]],
        "urgency": urgency,
        "urgency_confidence": urgency_conf,
        "is_emergency_override": is_emergency,
        "error": None,
    }


def model_metadata() -> dict:
    artifact = _load()
    return {
        "dept_accuracy": artifact.get("dept_accuracy"),
        "urgency_accuracy": artifact.get("urgency_accuracy"),
        "n_features": len(artifact.get("feature_names", [])),
    }
