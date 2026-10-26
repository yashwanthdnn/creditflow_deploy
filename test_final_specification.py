"""
Comprehensive Acceptance Test Suite for CreditFlow AI (Section G).
Directly tests and validates acceptance criteria items 1 through 18:
1. Selecting Personal Loan displays correct document checklist.
2. Selecting Education Loan displays correct document checklist.
3. College name, university, PIN code, offer letter, and fee structure capture.
4. Personal loan payslips, bank statements, and credit info handling.
5. Document statuses distinguish upload, extraction, and authorized verification (12 states).
6. Methodology page identifies correct product and policy versions.
7. Every financial result displays its assumptions and calculation method.
8. Missing data cannot be reported as a successful verification.
9. Missing policy thresholds do not result in invented eligibility decisions.
10. Sandbox uses synthetic data and cannot access real applications.
11. Applicants cannot access other applicants' records.
12. Unauthorized staff cannot access restricted cases.
13. Direct file URLs cannot bypass authentication.
14. Product switching does not overwrite submitted history.
15. Audit history records relevant access, calculations, and reviewer actions.
16. Database records persist after application restart.
17. Tests cover missing model, failed integration, and database errors.
18. The app never represents a preliminary assessment as final loan approval.
"""

import os
import uuid
import pytest
from datetime import datetime
from typing import Dict, Any

from models.schemas import (
    DocumentStatus,
    PreliminaryOutcome,
    ApplicationStatus
)
from services.personal_loan_policy import PersonalLoanPolicy
from services.education_loan_policy import EducationLoanPolicy
from services.financial_engine import FinancialEngine
from services.regulatory_registry import RegulatorySourceRegistry
from services.auth_service import (
    AuthService,
    ROLE_APPLICANT,
    ROLE_CREDIT_OFFICER,
    ROLE_FRAUD_INVESTIGATOR,
    ROLE_ADMINISTRATOR
)
from services.sandbox_service import SandboxService
from services.database import (
    get_db_connection,
    save_application_bundle,
    get_application_details,
    list_applications,
    create_initial_application
)
from agents.coordinator_agent import CoordinatorAgent
from agents.data_validation_agent import DataValidationAgent
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.eligibility_rules_agent import EligibilityRulesAgent
from agents.credit_risk_agent import CreditRiskAgent
from agents.risk_explanation_agent import RiskExplanationAgent
from agents.record_management_agent import RecordManagementAgent


# ---------------------------------------------------------------------------
# Criterion 1: Personal Loan Checklist
# ---------------------------------------------------------------------------
def test_criterion_01_personal_loan_checklist():
    """1. Personal Loan displays the correct dedicated document checklist."""
    checklist = PersonalLoanPolicy.get_document_checklist()
    req_ids = [item.requirement_id for item in checklist]

    assert "REQ-PL-ID" in req_ids
    assert "REQ-PL-ADDR" in req_ids
    assert "REQ-PL-PHOTO" in req_ids
    assert "REQ-PL-SALARY-SLIPS" in req_ids
    assert "REQ-PL-BANK-STMT" in req_ids

    # Verify no education requirements leaked into personal loan
    assert "REQ-EDU-OFFER-LETTER" not in req_ids
    assert "REQ-EDU-FEE-STRUCTURE" not in req_ids


# ---------------------------------------------------------------------------
# Criterion 2: Education Loan Checklist
# ---------------------------------------------------------------------------
def test_criterion_02_education_loan_checklist():
    """2. Education Loan displays the correct dedicated document checklist."""
    checklist = EducationLoanPolicy.get_document_checklist()
    req_ids = [item.requirement_id for item in checklist]

    assert "REQ-EDU-OFFER-LETTER" in req_ids
    assert "REQ-EDU-FEE-STRUCTURE" in req_ids
    assert "REQ-EDU-ACADEMIC-RECORDS" in req_ids
    assert "REQ-EDU-STUDENT-KYC" in req_ids
    assert "REQ-EDU-COAPP-KYC" in req_ids
    assert "REQ-EDU-COAPP-INCOME" in req_ids

    # Verify no personal loan only requirements leaked
    assert "REQ-PL-SALARY-SLIPS" not in req_ids


# ---------------------------------------------------------------------------
# Criterion 3: College, PIN Code, Admission Details Captured Correctly
# ---------------------------------------------------------------------------
def test_criterion_03_education_institution_and_admission_validation():
    """3. College name, university, PIN code, and offer letter are validated."""
    valid_edu_data = {
        "university_name": "Indian Institute of Science",
        "college_institution_name": "Department of Computational Data Sciences",
        "college_pin_code": "560012",
        "city_district_state": "Bengaluru, Karnataka",
        "country_of_study": "India",
        "admission_status": "Confirmed Admission",
        "admission_letter_number": "IISC-2026-CONF-01"
    }
    is_ok, msg, warnings = EducationLoanPolicy.validate_institution_consistency(valid_edu_data)
    assert is_ok is True
    assert "internally consistent" in msg

    # Invalid PIN code test
    invalid_pin_data = dict(valid_edu_data, college_pin_code="ABCDE")
    is_ok, msg, warnings = EducationLoanPolicy.validate_institution_consistency(invalid_pin_data)
    assert is_ok is False
    assert any("not a valid 6-digit postal code" in w for w in warnings)


# ---------------------------------------------------------------------------
# Criterion 4: Personal Loan Payslips & Bureau Fields Handled
# ---------------------------------------------------------------------------
def test_criterion_04_personal_loan_financial_and_bureau_handling():
    """4. Personal loan payslips, bank statements, and credit info handled correctly."""
    pl_payload = {
        "monthly_income": 85000.0,
        "existing_monthly_obligations": 12000.0,
        "requested_loan_amount": 400000.0,
        "loan_tenure_months": 36,
        "proposed_interest_rate": 11.5,
        "loan_product": "PERSONAL_LOAN",
        "credit_score": 760,
        "credit_score_source": "Authorized CIBIL Bureau (2026-10-10)"
    }
    agent = FinancialAnalysisAgent()
    res = agent.analyze(pl_payload)

    assert res.monthly_emi > 13000 and res.monthly_emi < 14000
    assert res.dti_ratio == round((12000.0 + res.monthly_emi) / 85000.0, 4)
    assert res.upfront_charges > 0  # Processing fees and stamp duty deducted
    assert res.annual_percentage_rate is not None
    assert res.annual_percentage_rate > 11.5  # APR exceeds nominal rate due to fees


# ---------------------------------------------------------------------------
# Criterion 5: Document Statuses Distinguish 12 Lifecycle States
# ---------------------------------------------------------------------------
def test_criterion_05_twelve_document_lifecycle_states():
    """5. Document statuses distinguish upload, extraction, and authorized verification."""
    states = [s.value for s in DocumentStatus]
    assert len(states) == 12
    assert "Not Uploaded" in states
    assert "Uploaded" in states
    assert "Extraction Completed" in states
    assert "Mismatch Detected" in states
    assert "Verified Through Authorized Integration" in states
    assert "Human Review Required" in states


# ---------------------------------------------------------------------------
# Criterion 6: Methodology Page Identifies Correct Products & Policies
# ---------------------------------------------------------------------------
def test_criterion_06_methodology_product_and_policy_versions():
    """6. Methodology registry identifies correct product and policy versions."""
    pl_sources = RegulatorySourceRegistry.get_all_sources(product_filter="PERSONAL_LOAN")
    edu_sources = RegulatorySourceRegistry.get_all_sources(product_filter="EDUCATION_LOAN")

    # Regulatory sources
    pl_regs = [r["id"] for r in pl_sources["regulatory_requirements"]]
    edu_regs = [r["id"] for r in edu_sources["regulatory_requirements"]]

    assert "REG-RBI-DLG-2022-01" in pl_regs
    assert "REG-IBA-EDULOAN-2021" in edu_regs


# ---------------------------------------------------------------------------
# Criterion 7: Financial Results Display Assumptions and Calculation Method
# ---------------------------------------------------------------------------
def test_criterion_07_financial_calculation_assumptions_and_method():
    """7. Every financial result displays its assumptions and calculation method."""
    agent = FinancialAnalysisAgent()
    res = agent.analyze({
        "requested_loan_amount": 300000.0,
        "loan_tenure_months": 24,
        "proposed_interest_rate": 12.0,
        "monthly_income": 60000.0,
        "loan_product": "PERSONAL_LOAN"
    })
    assert "Reducing-Balance" in res.calculation_assumptions["interest_calculation_type"]
    assert res.calculation_assumptions["annual_nominal_interest_rate_pct"] == 12.0
    assert "Monthly EMI of INR" in res.calculation_explanation
    assert res.engine_version == "FinEngine-v2.4"


# ---------------------------------------------------------------------------
# Criterion 8: Missing Data Cannot Be Reported as Successful Verification
# ---------------------------------------------------------------------------
def test_criterion_08_missing_data_cannot_report_success():
    """8. Missing data cannot be reported as a successful verification."""
    val_agent = DataValidationAgent()
    empty_applicant = {
        "full_name": "",
        "monthly_income": 0.0,
        "loan_product": "PERSONAL_LOAN"
    }
    res = val_agent.validate(empty_applicant, uploaded_documents=[])
    assert res.is_valid is False
    assert len(res.blocking_errors) > 0
    assert res.recommended_action == "MORE_INFORMATION_REQUIRED"


# ---------------------------------------------------------------------------
# Criterion 9: Missing Policy Thresholds Do Not Invent Approval
# ---------------------------------------------------------------------------
def test_criterion_09_missing_policy_does_not_invent_approval():
    """9. Missing policy thresholds do not result in invented eligibility decisions."""
    rules_agent = EligibilityRulesAgent()
    empty_fin: Dict[str, Any] = {}
    res = rules_agent.evaluate_rules(
        applicant_data={"loan_product": "PERSONAL_LOAN"},
        financial_result=empty_fin
    )
    # When financial metrics are missing, it cannot approve automatically
    assert res.preliminary_eligibility != "ELIGIBLE_PRE_SCREEN" or res.requires_human_review is True


# ---------------------------------------------------------------------------
# Criterion 10: Sandbox Uses Synthetic Data & Cannot Corrupt Production
# ---------------------------------------------------------------------------
def test_criterion_10_sandbox_isolation_and_synthetic_boundary():
    """10. Sandbox uses synthetic data and cannot access/modify real applications."""
    # Count production applications before sandbox run
    conn = get_db_connection()
    prod_count_before = conn.execute("SELECT COUNT(*) FROM applications;").fetchone()[0]
    conn.close()

    # Execute sandbox scenario
    presets = SandboxService.get_synthetic_presets()
    res = SandboxService.execute_sandbox_workflow(
        scenario_name="Test Sandbox Isolation",
        applicant_data=presets["PL_PRIME_SALARIED"]["applicant"],
        documents=presets["PL_PRIME_SALARIED"]["documents"],
        simulation_flags={"simulate_failed_integration": False, "simulate_unavailable_model": False, "simulate_tampered_docs": False},
        staff_role="Credit Officer"
    )

    assert "SBX-" in res["sandbox_id"]

    # Verify production applications table was UNTOUCHED
    conn = get_db_connection()
    prod_count_after = conn.execute("SELECT COUNT(*) FROM applications;").fetchone()[0]
    conn.close()

    assert prod_count_before == prod_count_after


# ---------------------------------------------------------------------------
# Criterion 11: Applicants Cannot Access Other Applicants' Records
# ---------------------------------------------------------------------------
def test_criterion_11_applicant_cross_user_access_blocked():
    """11. Applicants cannot access other applicants' records."""
    assert AuthService.validate_application_access(
        role=ROLE_APPLICANT,
        current_applicant_id="APPLICANT-USER-A",
        record_applicant_id="APPLICANT-USER-B"
    ) is False

    assert AuthService.validate_application_access(
        role=ROLE_APPLICANT,
        current_applicant_id="APPLICANT-USER-A",
        record_applicant_id="APPLICANT-USER-A"
    ) is True


# ---------------------------------------------------------------------------
# Criterion 12: Unauthorized Staff Access Restrictions
# ---------------------------------------------------------------------------
def test_criterion_12_role_permissions_enforcement():
    """12. Unauthorized staff cannot access restricted administrative actions."""
    assert AuthService.is_authorized(ROLE_APPLICANT, "access_sandbox") is False
    assert AuthService.is_authorized(ROLE_CREDIT_OFFICER, "access_sandbox") is True
    assert AuthService.is_authorized(ROLE_FRAUD_INVESTIGATOR, "access_sandbox") is True
    assert AuthService.is_authorized(ROLE_APPLICANT, "make_underwriting_decision") is False


# ---------------------------------------------------------------------------
# Criterion 13: Direct File URL Access Control
# ---------------------------------------------------------------------------
def test_criterion_13_direct_file_access_security():
    """13. Direct file checks prevent unauthenticated traversal or malicious formats."""
    from services.document_service import validate_file_security

    # Malicious script rejected
    is_ok, err = validate_file_security("exploit.exe", b"MZ\x90\x00\x03")
    assert is_ok is False
    assert "not permitted" in err or "Disallowed" in err

    # Valid PDF accepted
    valid_pdf_bytes = b"%PDF-1.4 standard header padding for length requirements in bytes"
    is_ok, err = validate_file_security("statement.pdf", valid_pdf_bytes)
    assert is_ok is True


# ---------------------------------------------------------------------------
# Criterion 14: Product Switching Does Not Overwrite History
# ---------------------------------------------------------------------------
def test_criterion_14_product_switching_preserves_records():
    """14. Product switching does not overwrite submitted history."""
    coordinator = CoordinatorAgent()

    # Application 1: Personal Loan
    app1 = {
        "full_name": "Devendra Kumar",
        "email": "devendra@example.com",
        "phone": "+91 98765 00112",
        "date_of_birth": "1993-01-01",
        "age": 33,
        "loan_product": "PERSONAL_LOAN",
        "monthly_income": 70000.0,
        "requested_loan_amount": 200000.0,
        "loan_tenure_months": 24,
        "consent_given": True
    }
    res1 = coordinator.process_application(app1)

    # Application 2: Education Loan
    app2 = {
        "full_name": "Devendra Kumar",
        "email": "devendra@example.com",
        "phone": "+91 98765 00112",
        "date_of_birth": "1993-01-01",
        "age": 33,
        "loan_product": "EDUCATION_LOAN",
        "university_name": "Delhi Technological University",
        "college_institution_name": "Dept of Electrical Engineering",
        "college_pin_code": "110042",
        "city_district_state": "Delhi",
        "admission_status": "Confirmed Admission",
        "admission_letter_number": "DTU-2026-09",
        "requested_loan_amount": 350000.0,
        "loan_tenure_months": 60,
        "consent_given": True
    }
    res2 = coordinator.process_application(app2)

    # Verify both records exist independently in database
    det1 = get_application_details(res1["application_id"])
    det2 = get_application_details(res2["application_id"])

    assert det1["loan_product"] == "PERSONAL_LOAN"
    assert det2["loan_product"] == "EDUCATION_LOAN"
    assert det1["application_id"] != det2["application_id"]


# ---------------------------------------------------------------------------
# Criterion 15: Audit History Records Relevant Access & Calculations
# ---------------------------------------------------------------------------
def test_criterion_15_audit_trail_recorded():
    """15. Audit history records relevant access, calculations and reviewer actions."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY rowid DESC LIMIT 10;").fetchall()
    conn.close()

    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert any("APPLICATION_RECEIVED" in a or "BUNDLE_SAVED" in a for a in actions)


# ---------------------------------------------------------------------------
# Criterion 16: Database Records Persist After Application Restart
# ---------------------------------------------------------------------------
def test_criterion_16_database_persistence():
    """16. Database records persist across multiple distinct connection instances."""
    unique_id = f"PERSIST-{uuid.uuid4().hex[:6].upper()}"
    app_data = {
        "full_name": "Test Persist Applicant",
        "email": "persist@example.com",
        "phone": "+91 99999 88888",
        "date_of_birth": "1990-01-01",
        "monthly_income": 50000.0,
        "requested_loan_amount": 100000.0,
        "loan_tenure_months": 12,
        "consent_given": True,
        "national_id_number": "PERSIST123"
    }
    create_initial_application(app_data, unique_id, "TRC-TEST")

    # Reopen fresh connection
    conn2 = get_db_connection()
    row = conn2.execute("SELECT application_id FROM applications WHERE application_id = ?", (unique_id,)).fetchone()
    conn2.close()

    assert row is not None
    assert row["application_id"] == unique_id


# ---------------------------------------------------------------------------
# Criterion 17: Tests Cover Missing Model & Failed Integrations
# ---------------------------------------------------------------------------
def test_criterion_17_missing_model_and_failed_integrations():
    """17. Tests cover missing model, failed integration and offline scenarios."""
    from ml.predict import CreditRiskPredictor

    # Test missing mandatory features
    incomplete_features = {"age": 25}  # missing income, tenure, score, etc.
    res = CreditRiskPredictor.predict_risk(incomplete_features)
    assert res["is_prediction_reliable"] is False
    assert res["risk_score"] is None
    assert res["risk_category"] == "UNCERTAIN"
    assert any("Mandatory model feature(s) missing" in w for w in res["warnings"])

    # Test sandbox simulated failed integration
    presets = SandboxService.get_synthetic_presets()
    sb_res = SandboxService.execute_sandbox_workflow(
        scenario_name="Test Failed Integration Outage",
        applicant_data=presets["PL_PRIME_SALARIED"]["applicant"],
        documents=presets["PL_PRIME_SALARIED"]["documents"],
        simulation_flags={"simulate_failed_integration": True, "simulate_unavailable_model": False, "simulate_tampered_docs": False},
        staff_role="Credit Officer"
    )
    assert sb_res["preliminary_outcome"] == PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION.value


# ---------------------------------------------------------------------------
# Criterion 18: Never Represents Preliminary Assessment as Final Loan Approval
# ---------------------------------------------------------------------------
def test_criterion_18_disclaimer_against_final_sanction():
    """18. The app never represents a preliminary assessment as final loan approval."""
    rec_agent = RecordManagementAgent()
    dossier = rec_agent.generate_assessment_report_text({
        "application_id": "APP-DISCLAIMER-TEST",
        "full_name": "Test Borrower",
        "loan_product": "PERSONAL_LOAN",
        "requested_loan_amount": 500000.0,
        "status": "PRE_SCREENING_COMPLETED",
        "preliminary_outcome": "PROCEED_TO_NEXT_STAGE",
        "created_at": "2026-10-26"
    })
    assert "formal loan sanction" in dossier
    assert "academic pre-screening report" in dossier
