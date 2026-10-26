"""
Configuration and Global Settings for AI Credit Assessment & Loan Pre-Screening System.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Storage Directories
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
UPLOADS_DIR = BASE_DIR / "uploads"
CONFIG_DIR = BASE_DIR / "config"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "loan_prescreening.db"))

# Security & Uploads
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"]
ALLOWED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

# Model Settings
MODEL_PATH = os.getenv("MODEL_PATH", str(ARTIFACTS_DIR / "credit_risk_model.joblib"))
MODEL_METADATA_PATH = os.getenv("MODEL_METADATA_PATH", str(ARTIFACTS_DIR / "model_metadata.json"))

# Financial & Lending Defaults
DEFAULT_ANNUAL_INTEREST_RATE = float(os.getenv("DEFAULT_ANNUAL_INTEREST_RATE", "12.0"))  # %
MAX_PERMITTED_DTI = float(os.getenv("MAX_PERMITTED_DTI", "0.55"))  # 55%
HIGH_RISK_DTI_THRESHOLD = float(os.getenv("HIGH_RISK_DTI_THRESHOLD", "0.50"))  # 50%
MIN_MONTHLY_INCOME = float(os.getenv("MIN_MONTHLY_INCOME", "15000.0"))
MIN_APPLICANT_AGE = int(os.getenv("MIN_APPLICANT_AGE", "18"))
MAX_APPLICANT_AGE = int(os.getenv("MAX_APPLICANT_AGE", "65"))

# Integration Environment Toggles (Mock vs Live)
SIMULATED_KYC_MODE = os.getenv("SIMULATED_KYC_MODE", "true").lower() == "true"
SIMULATED_BUREAU_MODE = os.getenv("SIMULATED_BUREAU_MODE", "true").lower() == "true"
SIMULATED_BANKING_MODE = os.getenv("SIMULATED_BANKING_MODE", "true").lower() == "true"
SIMULATED_DISBURSEMENT_MODE = os.getenv("SIMULATED_DISBURSEMENT_MODE", "true").lower() == "true"

# Disclaimers
ACADEMIC_PROTOTYPE_DISCLAIMER = (
    "This application is an academic AI-enabled loan-processing and pre-screening prototype. "
    "It does not replace an authorized lender's procedures, legal obligations, or required human oversight. "
    "External identity checks, credit-bureau access, e-signatures, and disbursement functions operate in "
    "simulation mode unless valid authorized integrations have been configured and tested."
)
