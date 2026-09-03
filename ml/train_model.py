"""
Trains two classifiers on the symptom dataset:
  1. department_clf  -- multi-class: which department should see this patient
  2. urgency_clf     -- multi-class: how urgently they should be seen

Both share the same multi-hot symptom feature matrix (one binary column per
known symptom). RandomForest was chosen over a linear model because symptom
combinations interact non-linearly (e.g. "chest pain" alone is very different
from "chest pain" + "shortness of breath" + "cold sweats" together), and over
a deep model because the dataset is small/synthetic and RandomForest is far
less prone to overfitting in that regime, while still giving us feature
importances for interpretability -- useful to show *why* a prediction was made,
which matters for anything adjacent to a medical context.
"""
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

from config import DATASET_PATH, MODEL_PATH
from ml.symptom_data import ALL_SYMPTOMS


def train():
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.exists(DATASET_PATH):
        from ml.generate_dataset import generate_dataset
        generate_dataset().to_csv(DATASET_PATH, index=False)

    df = pd.read_csv(DATASET_PATH)
    X = df[ALL_SYMPTOMS]
    y_dept = df["department"]
    y_urgency = df["urgency"]

    X_train, X_test, ydept_train, ydept_test, yurg_train, yurg_test = train_test_split(
        X, y_dept, y_urgency, test_size=0.2, random_state=42, stratify=y_dept
    )

    department_clf = RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=42, class_weight="balanced"
    )
    department_clf.fit(X_train, ydept_train)

    urgency_clf = RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=42, class_weight="balanced"
    )
    urgency_clf.fit(X_train, yurg_train)

    dept_preds = department_clf.predict(X_test)
    urg_preds = urgency_clf.predict(X_test)

    dept_acc = accuracy_score(ydept_test, dept_preds)
    urg_acc = accuracy_score(yurg_test, urg_preds)

    print(f"Department classifier accuracy: {dept_acc:.3f}")
    print(classification_report(ydept_test, dept_preds, zero_division=0))
    print(f"Urgency classifier accuracy: {urg_acc:.3f}")
    print(classification_report(yurg_test, urg_preds, zero_division=0))

    joblib.dump(
        {
            "department_clf": department_clf,
            "urgency_clf": urgency_clf,
            "feature_names": ALL_SYMPTOMS,
            "dept_accuracy": dept_acc,
            "urgency_accuracy": urg_acc,
        },
        MODEL_PATH,
    )
    print(f"Saved model artifact to {MODEL_PATH}")


if __name__ == "__main__":
    train()
