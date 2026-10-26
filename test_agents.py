"""
Automated unit tests for individual agents (Agents 2 through 7).
Tests valid inputs, missing fields, financial formulas, rule logic, ML bounds, and explanation generation.
"""

import pytest
from agents.data_validation_agent import DataValidationAgent
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.eligibility_rules_agent import EligibilityRulesAgent
from agents.credit_risk_agent import CreditRiskAgent
from agents.risk_explanation_agent import RiskExplanationAgent
from agents.record_management_agent import RecordManagementAgent


@pytest.fixture
def sample_valid_applicant():
    return {
        "application_id": "TEST-APP-001",
        "full_name": "Aditya Verma",
        "email": "aditya.verma@example.org",
        "phone": "+91-9876543210",
        "date_of_birth": "1994-06-15",
        "age": 31,
        "employment_type": "Salaried Full-Time",
        "employment_months": 36,
        "monthly_income": 65000.0,
        "existing_monthly_obligations": 8000.0,
        "dependents": 1,
        "loan_product": "PERSONAL_LOAN",
        "requested_loan_amount": 200000.0,
        "loan_tenure_months": 24,
        "proposed_interest_rate": 11.5,
        "credit_score": 750,
        "previous_defaults_count": 0,
        "consent_given": True,
        "national_id_number": "ABCDE1234F"
    }


def test_agent2_valid_applicant(sample_valid_applicant):
    """Test 1: Valid application data validation."""
    agent = DataValidationAgent()
    docs = [
        {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
        {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
        {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
        {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
    ]
    res = agent.validate(sample_valid_applicant, uploaded_documents=docs)
    assert res.is_valid is True
    assert len(res.blocking_errors) == 0
    assert res.recommended_action == "PROCEED"


def test_agent2_missing_mandatory_fields(sample_valid_applicant):
    """Test 2: Missing mandatory fields validation."""
    agent = DataValidationAgent()
    invalid_data = dict(sample_valid_applicant)
    invalid_data["full_name"] = ""
    invalid_data["monthly_income"] = None

    res = agent.validate(invalid_data)
    assert res.is_valid is False
    assert len(res.missing_fields) > 0
    assert res.recommended_action == "MORE_INFORMATION_REQUIRED"


def test_agent2_conflicting_document_income(sample_valid_applicant):
    """Test 5: Conflicting form and document data."""
    agent = DataValidationAgent()
    docs = [
        {
            "doc_category": "INCOME_PROOF",
            "status": "Uploaded",
            "extracted_fields": {"detected_monthly_income": 20000.0}  # Form has 65000
        }
    ]
    res = agent.validate(sample_valid_applicant, uploaded_documents=docs)
    assert len(res.inconsistency_flags) > 0
    assert res.recommended_action == "HUMAN_REVIEW_REQUIRED"


def test_agent3_financial_reducing_balance_emi(sample_valid_applicant):
    """Test 3: Reducing-balance EMI formula correctness."""
    agent = FinancialAnalysisAgent()
    res = agent.analyze(sample_valid_applicant)

    # Manual verification of EMI: P=200000, r=0.115/12, n=24
    # Expected EMI ~ 9370
    assert res.monthly_emi > 9000 and res.monthly_emi < 10000
    assert res.existing_obligations == 8000.0
    assert res.total_monthly_obligations == round(8000.0 + res.monthly_emi, 2)
    assert res.dti_ratio == round(res.total_monthly_obligations / 65000.0, 4)
    assert res.is_reliable is True


def test_agent3_zero_interest_case(sample_valid_applicant):
    """Test zero-interest loan tenure division."""
    agent = FinancialAnalysisAgent()
    data = dict(sample_valid_applicant)
    data["proposed_interest_rate"] = 0.0
    data["requested_loan_amount"] = 24000.0
    data["loan_tenure_months"] = 12

    res = agent.analyze(data)
    assert res.monthly_emi == 2000.0
    assert res.assumptions["zero_interest_handled"] is True


def test_agent3_invalid_negative_financial_inputs(sample_valid_applicant):
    """Test handling of impossible zero/negative income."""
    agent = FinancialAnalysisAgent()
    data = dict(sample_valid_applicant)
    data["monthly_income"] = 0.0

    res = agent.analyze(data)
    assert res.is_reliable is False
    assert len(res.warnings) > 0


def test_agent4_eligibility_rules_pass(sample_valid_applicant):
    """Test rule evaluations when parameters pass thresholds."""
    agent = EligibilityRulesAgent()
    fin_res = {"dti_ratio": 0.28, "loan_to_annual_income": 0.5, "monthly_emi": 9370.0}
    res = agent.evaluate_rules(sample_valid_applicant, financial_result=fin_res)

    assert res.rules_evaluated > 0
    assert res.rules_passed >= 6
    assert res.preliminary_eligibility == "ELIGIBLE_PRE_SCREEN"


def test_agent4_blocking_rule_failure(sample_valid_applicant):
    """Test blocking rule failure when applicant is underage."""
    agent = EligibilityRulesAgent()
    underage_data = dict(sample_valid_applicant)
    underage_data["age"] = 16

    res = agent.evaluate_rules(underage_data)
    assert res.requires_human_review is True
    assert res.preliminary_eligibility == "INELIGIBLE_RULES_FAIL"


def test_agent5_credit_risk_scoring(sample_valid_applicant):
    """Test ML prediction produces valid default probability."""
    agent = CreditRiskAgent()
    fin_res = {"dti_ratio": 0.28}
    res = agent.assess_risk(sample_valid_applicant, financial_data=fin_res)

    assert res.risk_score is not None
    assert 0.0 <= res.risk_score <= 1.0
    assert res.risk_category in ["LOW", "MEDIUM", "HIGH"]
    assert res.model_version != ""
    assert res.is_prediction_reliable is True


def test_agent6_explanation_and_recommendation(sample_valid_applicant):
    """Test Agent 6 compiles evidence trail and disclaimer."""
    agent = RiskExplanationAgent()
    val_data = {"is_valid": True, "blocking_errors": [], "warnings": [], "inconsistency_flags": [], "duplicate_flags": []}
    fin_data = {"dti_ratio": 0.25, "net_disposable_income": 40000.0, "monthly_emi": 9000.0, "is_reliable": True}
    rules_data = {"rules_passed": 8, "rules_failed": 0, "rule_items": [], "requires_human_review": False}
    risk_data = {"risk_category": "LOW", "risk_score": 0.12, "is_prediction_reliable": True}

    res = agent.generate_recommendation(
        applicant_data=sample_valid_applicant,
        validation_data=val_data,
        financial_data=fin_data,
        rules_data=rules_data,
        risk_data=risk_data
    )

    assert res.preliminary_outcome.value == "PROCEED_TO_NEXT_STAGE"
    assert len(res.positive_factors) > 0
    assert len(res.evidence_trail) > 0
    assert "academic" in res.disclaimer.lower()
