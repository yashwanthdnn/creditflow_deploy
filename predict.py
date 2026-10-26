"""
Inference engine for Credit Risk Agent.
Loads trained pipeline, checks input bounds, computes probability of default,
and maps probabilities to risk tiers (LOW, MEDIUM, HIGH) with limitation warnings.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
import joblib

from config.settings import MODEL_PATH, MODEL_METADATA_PATH
from ml.train_model import FEATURE_COLUMNS, train_and_compare_models


class CreditRiskPredictor:
    _instance = None
    _pipeline = None
    _metadata = None

    @classmethod
    def get_pipeline(cls):
        """Lazy load or train baseline model pipeline."""
        if cls._pipeline is None:
            if not Path(MODEL_PATH).exists():
                # Automatically train baseline model on demand
                cls._metadata = train_and_compare_models()
            cls._pipeline = joblib.load(MODEL_PATH)
            if cls._metadata is None and Path(MODEL_METADATA_PATH).exists():
                with open(MODEL_METADATA_PATH, "r") as f:
                    cls._metadata = json.load(f)
        return cls._pipeline, cls._metadata or {}

    @classmethod
    def predict_risk(cls, applicant_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute credit risk prediction given applicant and financial fields.
        Returns risk score (default probability), risk tier, warnings, and limitations.
        """
        pipeline, metadata = cls.get_pipeline()
        warnings = []
        limitations = [
            "Model is an academic demonstration trained on synthetic credit distributions.",
            "Not authorized for unmonitored real-world credit sanctioning.",
            "Historical pattern correlation does not constitute legal proof of repayment capacity."
        ]

        # Extract & validate features
        features = {}
        missing = []
        for col in FEATURE_COLUMNS:
            val = applicant_dict.get(col)
            if val is None:
                missing.append(col)
            else:
                features[col] = float(val)

        if missing:
            return {
                "risk_score": None,
                "risk_category": "UNCERTAIN",
                "model_version": metadata.get("model_version", "v1.0-uncalibrated"),
                "model_name": metadata.get("selected_model", "Unknown"),
                "features_used": FEATURE_COLUMNS,
                "inference_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
                "is_prediction_reliable": False,
                "limitations": limitations,
                "warnings": [f"Mandatory model feature(s) missing: {', '.join(missing)}"],
                "explanation_notes": "Refused inference because mandatory credit risk features were absent."
            }

        # Out of range detection
        if features["age"] < 18 or features["age"] > 80:
            warnings.append(f"Applicant age ({features['age']}) is near boundary limits.")
        if features["dti_ratio"] > 1.0:
            warnings.append(f"DTI ratio ({round(features['dti_ratio']*100, 1)}%) exceeds 100% of declared monthly income.")
        if features["credit_score"] < 400 or features["credit_score"] > 850:
            warnings.append(f"Credit bureau score ({features['credit_score']}) is in extreme tail range.")

        # Inference
        df_row = pd.DataFrame([features])
        try:
            if hasattr(pipeline, "predict_proba"):
                probs = pipeline.predict_proba(df_row[FEATURE_COLUMNS])[0]
                prob_default = float(probs[1])
            else:
                pred = pipeline.predict(df_row[FEATURE_COLUMNS])[0]
                prob_default = 0.85 if pred == 1 else 0.15

            # Categorize
            if prob_default < 0.25:
                category = "LOW"
            elif prob_default < 0.50:
                category = "MEDIUM"
            else:
                category = "HIGH"

            is_reliable = len(warnings) == 0

            return {
                "risk_score": round(prob_default, 4),
                "risk_category": category,
                "model_version": metadata.get("model_version", "v1.2-academic"),
                "model_name": metadata.get("selected_model", "RandomForest"),
                "features_used": FEATURE_COLUMNS,
                "inference_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
                "is_prediction_reliable": is_reliable,
                "limitations": limitations,
                "warnings": warnings,
                "explanation_notes": (
                    f"Estimated default probability is {round(prob_default * 100, 1)}% "
                    f"({category} risk band) based on credit score, DTI ratio, and repayment history."
                )
            }
        except Exception as e:
            return {
                "risk_score": None,
                "risk_category": "UNCERTAIN",
                "model_version": metadata.get("model_version", "v1.0-error"),
                "model_name": "InferenceException",
                "features_used": FEATURE_COLUMNS,
                "inference_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
                "is_prediction_reliable": False,
                "limitations": limitations,
                "warnings": [f"Inference computation error: {str(e)}"],
                "explanation_notes": "Model prediction failed during runtime execution."
            }
