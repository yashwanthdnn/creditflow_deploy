"""
Credit Risk ML Model Training and Model Comparison Pipeline.
Compares Logistic Regression, Decision Tree, and Random Forest on credit risk features.
Saves the best-performing model pipeline and training metadata with evaluation metrics.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from config.settings import ARTIFACTS_DIR, MODEL_PATH, MODEL_METADATA_PATH, DATA_DIR

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "age",
    "monthly_income",
    "requested_loan_amount",
    "loan_tenure_months",
    "existing_monthly_obligations",
    "employment_months",
    "dependents",
    "credit_score",
    "previous_defaults_count",
    "dti_ratio"
]


def generate_synthetic_credit_dataset(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate a realistic credit risk dataset with realistic economic distributions
    and correlated default outcomes based on credit score, DTI, and default history.
    """
    np.random.seed(random_state)

    age = np.random.randint(18, 65, size=n_samples)
    monthly_income = np.random.lognormal(mean=10.6, sigma=0.6, size=n_samples)  # ~15k to 200k
    monthly_income = np.clip(monthly_income, 12000, 400000)

    requested_loan_amount = np.random.lognormal(mean=12.2, sigma=0.8, size=n_samples)
    requested_loan_amount = np.clip(requested_loan_amount, 25000, 2500000)

    loan_tenure_months = np.random.choice([12, 24, 36, 48, 60, 84, 120], size=n_samples)
    existing_obligations = monthly_income * np.random.beta(a=1.5, b=5.0, size=n_samples)
    employment_months = np.random.exponential(scale=36, size=n_samples)
    employment_months = np.clip(employment_months, 1, 360).astype(int)
    dependents = np.random.choice([0, 1, 2, 3, 4], p=[0.40, 0.25, 0.20, 0.10, 0.05], size=n_samples)

    # Credit score normally distributed around 680, clipped 300 to 850
    credit_score = np.random.normal(loc=680, scale=80, size=n_samples).astype(int)
    credit_score = np.clip(credit_score, 300, 850)

    previous_defaults = np.random.choice([0, 1, 2, 3], p=[0.82, 0.12, 0.04, 0.02], size=n_samples)

    # Compute rough proposed monthly EMI at 12% annual rate
    r = (12.0 / 100.0) / 12.0
    proposed_emi = (requested_loan_amount * r * (1 + r)**loan_tenure_months) / ((1 + r)**loan_tenure_months - 1)
    dti_ratio = (existing_obligations + proposed_emi) / monthly_income

    # Deterministic risk logit with realistic economic behavior
    logit = (
        - 0.009 * (credit_score - 650)
        + 3.2 * (dti_ratio - 0.40)
        + 1.4 * previous_defaults
        - 0.000008 * (monthly_income - 40000)
        - 0.015 * (employment_months - 24)
        + 0.15 * dependents
    )
    prob_default = 1.0 / (1.0 + np.exp(-logit))
    # Add minor stochastic perturbation
    prob_default = np.clip(prob_default, 0.01, 0.99)
    default_label = (np.random.rand(n_samples) < prob_default).astype(int)

    df = pd.DataFrame({
        "age": age,
        "monthly_income": monthly_income.round(2),
        "requested_loan_amount": requested_loan_amount.round(2),
        "loan_tenure_months": loan_tenure_months,
        "existing_monthly_obligations": existing_obligations.round(2),
        "employment_months": employment_months,
        "dependents": dependents,
        "credit_score": credit_score,
        "previous_defaults_count": previous_defaults,
        "dti_ratio": dti_ratio.round(4),
        "target_default": default_label
    })

    return df


def train_and_compare_models():
    """Train Logistic Regression, Decision Tree, and Random Forest; save best model & report."""
    raw_data_path = DATA_DIR / "synthetic_credit_data.csv"
    if raw_data_path.exists():
        df = pd.read_csv(raw_data_path)
    else:
        df = generate_synthetic_credit_dataset()
        df.to_csv(raw_data_path, index=False)

    X = df[FEATURE_COLUMNS]
    y = df["target_default"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    models = {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42))
        ]),
        "DecisionTree": Pipeline([
            ("clf", DecisionTreeClassifier(max_depth=6, min_samples_leaf=15, random_state=42))
        ]),
        "RandomForest": Pipeline([
            ("clf", RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=10, random_state=42, n_jobs=1))
        ])
    }

    results = {}
    best_model_name = "RandomForest"
    best_f1 = -1.0
    best_pipeline = None

    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[name] = {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": cm
        }

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_pipeline = pipeline

    # Save best model
    joblib.dump(best_pipeline, MODEL_PATH)

    metadata = {
        "model_version": "v1.2-academic",
        "selected_model": best_model_name,
        "training_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
        "target_definition": "1 = Default on loan within 24 months, 0 = Non-default",
        "features_used": FEATURE_COLUMNS,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "comparison_metrics": results,
        "disclaimer": (
            "This model was trained on an academic synthetic credit distribution. "
            "It must not be utilized for unmonitored production loan underwriting."
        )
    }

    with open(MODEL_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model comparison completed. Best: {best_model_name} (F1: {best_f1:.4f}). Saved to {MODEL_PATH}")
    return metadata


if __name__ == "__main__":
    meta = train_and_compare_models()
    print("Training Complete. Metadata summary:")
    print(json.dumps(meta["comparison_metrics"], indent=2))
