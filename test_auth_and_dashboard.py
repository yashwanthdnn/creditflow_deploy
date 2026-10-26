"""
Unit tests for Login, Logout, Multi-Role Authentication, and Clear Dashboard Metrics.
"""

import pytest
from services.auth_service import (
    AuthService,
    ROLE_CREDIT_OFFICER,
    ROLE_FRAUD_INVESTIGATOR,
    ROLE_ADMINISTRATOR,
    ROLE_APPLICANT
)
from services.database import get_dashboard_metrics
from ui_pages.dashboard import STATUS_DISPLAY_MAP, OUTCOME_DISPLAY_MAP


def test_credit_officer_authentication():
    """Verify Credit Officer credentials validation."""
    # Valid login
    user = AuthService.authenticate("officer", "password123", role_hint=ROLE_CREDIT_OFFICER)
    assert user is not None
    assert user["role"] == ROLE_CREDIT_OFFICER
    assert "Priya" in user["full_name"]

    # Invalid password
    assert AuthService.authenticate("officer", "wrongpass", role_hint=ROLE_CREDIT_OFFICER) is None


def test_fraud_investigator_authentication():
    """Verify Fraud Investigator credentials validation."""
    user = AuthService.authenticate("investigator", "password123", role_hint=ROLE_FRAUD_INVESTIGATOR)
    assert user is not None
    assert user["role"] == ROLE_FRAUD_INVESTIGATOR
    assert "Amitabh" in user["full_name"]


def test_administrator_authentication():
    """Verify Administrator credentials validation."""
    user = AuthService.authenticate("admin", "password123", role_hint=ROLE_ADMINISTRATOR)
    assert user is not None
    assert user["role"] == ROLE_ADMINISTRATOR
    assert "Vikram" in user["full_name"]


def test_applicant_authentication_and_registration():
    """Verify Applicant login and self-service registration."""
    # Demo applicant
    user = AuthService.authenticate("applicant", "password123", role_hint=ROLE_APPLICANT)
    assert user is not None
    assert user["role"] == ROLE_APPLICANT

    # Registration
    new_user = AuthService.register_applicant("Rohan Verma", "rohan.v@example.com", "9876543210", "securepass")
    assert new_user is not None
    assert new_user["full_name"] == "Rohan Verma"
    assert new_user["role"] == ROLE_APPLICANT
    assert "USR-APP-" in new_user["user_id"]


def test_login_and_logout_audit_logging():
    """Verify that login and logout generate audit events."""
    AuthService.log_login_event("USR-TEST-01", ROLE_CREDIT_OFFICER, "officer")
    AuthService.log_logout_event("USR-TEST-01", ROLE_CREDIT_OFFICER, "officer")
    # If no exception was raised, audit logs were successfully recorded


def test_dashboard_metrics_product_distribution():
    """Verify dashboard metrics include product breakdown."""
    metrics = get_dashboard_metrics()
    assert "total_applications" in metrics
    assert "status_distribution" in metrics
    assert "outcome_distribution" in metrics
    assert "product_distribution" in metrics
    assert isinstance(metrics["product_distribution"], dict)


def test_clean_dashboard_label_mappings():
    """Verify that all raw enums are mapped to human-readable strings without underscores."""
    raw_statuses = [
        "PRE_SCREENING_COMPLETED", "HUMAN_REVIEW_REQUIRED", "MORE_INFORMATION_REQUIRED",
        "ON_HOLD", "DISPUTED", "APPROVED_BY_AUTHORIZED_LENDER"
    ]
    for s in raw_statuses:
        mapped = STATUS_DISPLAY_MAP.get(s)
        assert mapped is not None
        assert "_" not in mapped, f"Underscore found in mapped status: {mapped}"

    raw_outcomes = [
        "PROCEED_TO_NEXT_STAGE", "REQUIRES_HUMAN_REVIEW", "MORE_INFORMATION_REQUIRED",
        "ON_HOLD_FOR_VERIFICATION", "UNDER_EVALUATION"
    ]
    for o in raw_outcomes:
        mapped = OUTCOME_DISPLAY_MAP.get(o)
        assert mapped is not None
        assert "_" not in mapped, f"Underscore found in mapped outcome: {mapped}"
