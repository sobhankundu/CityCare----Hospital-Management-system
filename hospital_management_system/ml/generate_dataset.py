"""
Generates a synthetic labelled dataset for training the symptom-checker model.

There's no public, licensable "which department does this symptom belong to"
dataset suitable for a portfolio project, so we synthesise one programmatically
from the DEPARTMENT_SYMPTOMS domain mapping: for each sample we pick a
department, sample a realistic subset of its symptoms, occasionally mix in an
unrelated "noise" symptom (patients don't always report cleanly), and derive
an urgency label from symptom severity. This keeps the whole pipeline
reproducible and inspectable end to end -- generation -> training -> inference
-- which is exactly what you'd want to explain in an interview.
"""
import random

import numpy as np
import pandas as pd

from ml.symptom_data import (
    ALL_SYMPTOMS, DEPARTMENT_SYMPTOMS, EMERGENCY_SYMPTOMS, HIGH_RISK_SYMPTOMS,
)
from config import DATASET_PATH

random.seed(42)

SAMPLES_PER_DEPARTMENT = 220


def _derive_urgency(symptoms: set) -> str:
    if symptoms & EMERGENCY_SYMPTOMS:
        return "Emergency"
    if symptoms & HIGH_RISK_SYMPTOMS:
        return "High"
    # Below the "high risk" threshold, urgency mostly tracks how many
    # symptoms are present at once. A small amount of label noise is kept
    # in to mimic real-world ambiguity, without erasing the boundary
    # entirely (that erasure is what made "Medium" unlearnable initially).
    base = "Medium" if len(symptoms) >= 4 else "Low"
    if random.random() < 0.08:
        base = "Low" if base == "Medium" else "Medium"
    return base


def _weighted_sample_without_replacement(population: list, k: int) -> list:
    """Like random.sample, but emergency symptoms are under-weighted so they
    show up in a realistic minority of cases rather than uniformly at random.
    """
    weights = np.array(
        [0.35 if s in EMERGENCY_SYMPTOMS else 1.0 for s in population]
    )
    probs = weights / weights.sum()
    idx = np.random.choice(len(population), size=k, replace=False, p=probs)
    return [population[i] for i in idx]


def _sample_row(department: str) -> dict:
    dept_symptoms = DEPARTMENT_SYMPTOMS[department]
    k = random.randint(2, min(5, len(dept_symptoms)))
    chosen = set(_weighted_sample_without_replacement(dept_symptoms, k))

    # 15% chance of one unrelated "noise" symptom from another department,
    # simulating real patients reporting a comorbid or unrelated complaint.
    if random.random() < 0.15:
        noise_pool = [s for s in ALL_SYMPTOMS if s not in dept_symptoms]
        chosen.add(random.choice(noise_pool))

    urgency = _derive_urgency(chosen)
    row = {symptom: int(symptom in chosen) for symptom in ALL_SYMPTOMS}
    row["department"] = department
    row["urgency"] = urgency
    return row


def generate_dataset() -> pd.DataFrame:
    rows = []
    for department in DEPARTMENT_SYMPTOMS:
        for _ in range(SAMPLES_PER_DEPARTMENT):
            rows.append(_sample_row(department))
    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv(DATASET_PATH, index=False)
    print(f"Wrote {len(df)} rows x {df.shape[1]} columns to {DATASET_PATH}")
    print(df["department"].value_counts())
    print(df["urgency"].value_counts())
