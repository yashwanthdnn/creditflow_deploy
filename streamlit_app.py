"""
CreditFlow AI — Streamlit Cloud Production Deployment Entry Point
Automatically resolves package layout (whether nested or flattened by GitHub upload)
and executes the main application (app.py).
"""

import sys
import os
import shutil
import runpy
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure required persistent storage directories exist
(ROOT_DIR / "data").mkdir(parents=True, exist_ok=True)
(ROOT_DIR / "artifacts").mkdir(parents=True, exist_ok=True)
(ROOT_DIR / "uploads").mkdir(parents=True, exist_ok=True)

# Self-healing package layout:
# If files were uploaded flat to the GitHub root directory, automatically organize them into packages
PACKAGE_MAP = {
    "config": ["settings.py", "loan_rules.yaml", "document_requirements.yaml"],
    "services": [
        "auth_service.py", "database.py", "financial_engine.py", "personal_loan_policy.py",
        "education_loan_policy.py", "regulatory_registry.py", "sandbox_service.py",
        "document_service.py", "integration_service.py", "audit_service.py", "decision_policy.py",
        "notification_service.py", "ocr_service.py"
    ],
    "ui_pages": [
        "dashboard.py", "login.py", "new_application.py", "applications.py",
        "document_verification.py", "human_review.py", "fraud_investigation.py",
        "complaints_disputes.py", "agent_logs.py", "analytics.py", "responsible_ai.py",
        "methodology.py", "sandbox.py"
    ],
    "agents": [
        "coordinator_agent.py", "data_validation_agent.py", "financial_analysis_agent.py",
        "eligibility_rules_agent.py", "credit_risk_agent.py", "risk_explanation_agent.py",
        "record_management_agent.py"
    ],
    "models": ["schemas.py", "model_loader.py"],
    "ml": ["predict.py", "train_model.py", "evaluate_model.py", "model_loader.py"],
    "artifacts": ["credit_risk_model.joblib", "model_metadata.json"],
    "data": ["loan_prescreening.db", "sandbox_evaluations.db", "synthetic_credit_data.csv"]
}

for pkg_name, file_list in PACKAGE_MAP.items():
    target_dir = ROOT_DIR / pkg_name
    target_dir.mkdir(parents=True, exist_ok=True)
    init_file = target_dir / "__init__.py"
    if not init_file.exists():
        try:
            init_file.write_text(f'"""{pkg_name} package"""\n', encoding="utf-8")
        except Exception:
            pass
    for fname in file_list:
        src_candidate = ROOT_DIR / fname
        dest_target = target_dir / fname
        if src_candidate.exists() and not dest_target.exists():
            try:
                shutil.copy2(src_candidate, dest_target)
            except Exception:
                pass

# Run app.py in the main namespace
app_path = ROOT_DIR / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
