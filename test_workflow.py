"""
End-to-End Orchestrator Workflow Tests.
Verifies the Coordinator Agent across all 7 steps, state transitions,
auto-progression, exception escalations, pauses, and batch assessments.
"""

import uuid
import pytest
from agents.coordinator_agent import CoordinatorAgent
from models.schemas import ApplicationStatus, PreliminaryOutcome
from services.database import get_application_details


@pytest.fixture
def coordinator():
    return CoordinatorAgent()


def test_straightforward_auto_progression(coordinator):
    """Test 1: Complete healthy application proceeds to next stage automatically."""
    unique_suffix = uuid.uuid4().hex[:6].upper()
    applicant = {
        "full_name": f"Rohan Deshmukh {unique_suffix}",
        "email": f"rohan.{unique_suffix.lower()}@example.com",
        "phone": "+91-9876543211",
        "date_of_birth": "1992-04-10",
        "age": 33,
        "employment_type": "Salaried Full-Time",
        "employment_months": 48,
        "monthly_income": 95000.0,
        "existing_monthly_obligations": 5000.0,
        "dependents": 1,
        "loan_product": "PERSONAL_LOAN",
        "requested_loan_amount": 250000.0,
        "loan_tenure_months": 36,
        "proposed_interest_rate": 10.5,
        "credit_score": 780,
        "previous_defaults_count": 0,
        "consent_given": True,
        "national_id_number": f"RD{unique_suffix}"
    }
    docs = [
        {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
        {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
        {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
        {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
    ]

    result = coordinator.process_application(applicant, uploaded_documents=docs)

    assert result["status"] == ApplicationStatus.PRE_SCREENING_COMPLETED.value
    assert result["preliminary_outcome"] == PreliminaryOutcome.PROCEED_TO_NEXT_STAGE.value
    assert len(result["agent_logs"]) == 6  # All 6 sub-agents executed sequentially

    # Verify SQLite persistence
    app_id = result["application_id"]
    details = get_application_details(app_id)
    assert details is not None
    assert "Rohan Deshmukh" in details["full_name"]
    assert details["financial_result"] is not None


def test_high_risk_escalation(coordinator):
    """Test 9: High risk / high DTI escalates to Human Review."""
    applicant = {
        "full_name": "Suresh Raina",
        "email": "suresh.raina@example.com",
        "phone": "+91-9876543212",
        "date_of_birth": "1988-11-20",
        "age": 37,
        "employment_type": "Self-Employed Business",
        "employment_months": 12,
        "monthly_income": 30000.0,
        "existing_monthly_obligations": 18000.0,  # 60% DTI already
        "dependents": 3,
        "loan_product": "PERSONAL_LOAN",
        "requested_loan_amount": 500000.0,  # High loan relative to income
        "loan_tenure_months": 24,
        "proposed_interest_rate": 14.0,
        "credit_score": 520,  # Poor credit
        "previous_defaults_count": 2,
        "consent_given": True,
        "national_id_number": "SRDEF5544P"
    }

    result = coordinator.process_application(applicant)

    assert result["status"] == ApplicationStatus.HUMAN_REVIEW_REQUIRED.value
    assert result["preliminary_outcome"] == PreliminaryOutcome.REQUIRES_HUMAN_REVIEW.value


def test_missing_information_pauses_workflow(coordinator):
    """Test 2 & 14: Incomplete inputs pause workflow with MORE_INFORMATION_REQUIRED."""
    incomplete_applicant = {
        "full_name": "Pooja Hegde",
        "email": "pooja.h@example.com",
        "phone": "+91-9876543213",
        "date_of_birth": "1998-02-14",
        "age": 27,
        "monthly_income": 50000.0,
        "requested_loan_amount": 100000.0,
        "loan_tenure_months": 12,
        "consent_given": True,
        # Missing documents
    }

    result = coordinator.process_application(incomplete_applicant, uploaded_documents=[])

    assert result["status"] == ApplicationStatus.MORE_INFORMATION_REQUIRED.value
    assert result["preliminary_outcome"] == PreliminaryOutcome.MORE_INFORMATION_REQUIRED.value

    # Resubmission / Correction scenario
    corrected_docs = [
        {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
        {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
        {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
        {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
    ]
    incomplete_applicant["credit_score"] = 720
    resumed_result = coordinator.process_application(incomplete_applicant, uploaded_documents=corrected_docs)
    assert resumed_result["status"] in [
        ApplicationStatus.PRE_SCREENING_COMPLETED.value,
        ApplicationStatus.HUMAN_REVIEW_REQUIRED.value
    ]


def test_active_dispute_places_on_hold(coordinator):
    """Test 11: Applicant with an open dispute is placed ON_HOLD."""
    applicant = {
        "full_name": "Karan Johar",
        "email": "karan.j@example.com",
        "phone": "+91-9876543214",
        "date_of_birth": "1990-01-01",
        "age": 35,
        "monthly_income": 80000.0,
        "requested_loan_amount": 150000.0,
        "loan_tenure_months": 12,
        "consent_given": True,
        "credit_score": 740,
        "national_id_number": "KJDISP1122Q"
    }

    result = coordinator.process_application(applicant, has_open_dispute=True)
    assert result["status"] == ApplicationStatus.DISPUTED.value
    assert result["preliminary_outcome"] == PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION.value


def test_what_if_analysis(coordinator):
    """Test 15: What-if analysis altering tenure to reduce monthly DTI."""
    base_applicant = {
        "full_name": "Simulated WhatIf Candidate",
        "email": "whatif@example.com",
        "phone": "+91-9999900000",
        "date_of_birth": "1995-05-05",
        "age": 30,
        "monthly_income": 40000.0,
        "requested_loan_amount": 300000.0,
        "loan_tenure_months": 12,  # Short tenure -> High EMI ~ 26,654 (DTI ~ 66%)
        "proposed_interest_rate": 12.0,
        "credit_score": 710,
        "consent_given": True
    }

    # Run 1: High stress
    run1 = coordinator.process_application(base_applicant)
    dti1 = run1["financial_result"]["dti_ratio"]
    assert dti1 > 0.55

    # Run 2: Extended tenure to 48 months -> Low EMI ~ 7,900 (DTI ~ 20%)
    stretched_applicant = dict(base_applicant)
    stretched_applicant["loan_tenure_months"] = 48
    run2 = coordinator.process_application(stretched_applicant)
    dti2 = run2["financial_result"]["dti_ratio"]
    assert dti2 < 0.30
    assert dti2 < dti1
