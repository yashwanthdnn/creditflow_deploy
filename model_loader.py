"""
Model loader utility for loading trained artifacts and configuration metadata.
"""

from pathlib import Path
import json
import joblib
from config.settings import MODEL_PATH, MODEL_METADATA_PATH


def load_credit_risk_model():
    """Load trained model pipeline and metadata."""
    if not Path(MODEL_PATH).exists():
        return None, None

    model = joblib.load(MODEL_PATH)
    meta = {}
    if Path(MODEL_METADATA_PATH).exists():
        with open(MODEL_METADATA_PATH, "r") as f:
            meta = json.load(f)

    return model, meta
