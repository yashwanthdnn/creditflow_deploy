"""
Model Evaluation and Metrics Reporting Script.
Loads the trained pipeline, computes cross-validation or holdout metrics,
and renders evaluation reports.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import pandas as pd
import joblib
from sklearn.metrics import classification_report, roc_auc_score

from config.settings import MODEL_PATH, MODEL_METADATA_PATH, DATA_DIR
from ml.train_model import FEATURE_COLUMNS, generate_synthetic_credit_dataset


def evaluate_trained_pipeline():
    """Load model and compute detailed classification statistics."""
    if not Path(MODEL_PATH).exists():
        return {"error": "Trained model artifact not found. Please run ml/train_model.py first."}

    pipeline = joblib.load(MODEL_PATH)

    data_path = DATA_DIR / "synthetic_credit_data.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
    else:
        df = generate_synthetic_credit_dataset(n_samples=1000)

    X = df[FEATURE_COLUMNS]
    y = df["target_default"]

    y_pred = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1] if hasattr(pipeline, "predict_proba") else None

    report = classification_report(y, y_pred, output_dict=True)
    auc = float(roc_auc_score(y, y_proba)) if y_proba is not None else None

    meta = {}
    if Path(MODEL_METADATA_PATH).exists():
        with open(MODEL_METADATA_PATH, "r") as f:
            meta = json.load(f)

    return {
        "model_version": meta.get("model_version", "v1.0"),
        "selected_model": meta.get("selected_model", "RandomForest"),
        "features": FEATURE_COLUMNS,
        "sample_count": len(df),
        "roc_auc": round(auc, 4) if auc else None,
        "classification_report": report,
        "comparison_metrics": meta.get("comparison_metrics", {})
    }


if __name__ == "__main__":
    res = evaluate_trained_pipeline()
    print(json.dumps(res, indent=2))
