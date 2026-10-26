"""
Database and Transactional Persistence Tests.
Tests parameterized queries, audit trail logging, fraud case tracking, and human review recording.
"""

from services.database import (
    get_db_connection,
    record_human_review,
    create_fraud_case,
    resolve_fraud_case,
    create_complaint_case,
    resolve_complaint_case,
    get_application_details,
    list_applications
)


def test_database_table_existence():
    """Verify that all normalized tables are created properly."""
    conn = get_db_connection()
    tables = [
        "applicants", "applications", "documents", "agent_runs",
        "validation_results", "financial_assessments", "rule_evaluations",
        "risk_assessments", "recommendations", "human_reviews",
        "fraud_cases", "complaints_disputes", "audit_logs"
    ]
    cursor = conn.cursor()
    for table in tables:
        row = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        assert row is not None, f"Table {table} does not exist in schema"
    conn.close()


def test_human_review_recorded_separately():
    """Test 20: Authorized reviewer records approval/rejection separately from AI."""
    app_id = "TEST-REV-APP-099"
    # Seed minimal applicant & app row
    conn = get_db_connection()
    with conn:
        conn.execute("""
        INSERT OR REPLACE INTO applicants (applicant_id, full_name, email, phone, date_of_birth, age, employment_type, monthly_income)
        VALUES ('AP-99', 'Test Underwriter Target', 'rev@target.org', '1234567890', '1990-01-01', 35, 'Salaried', 50000)
        """)
        conn.execute("""
        INSERT OR REPLACE INTO applications (application_id, applicant_id, loan_product, requested_loan_amount, loan_tenure_months, proposed_interest_rate, consent_given, status, preliminary_outcome)
        VALUES (?, 'AP-99', 'PERSONAL_LOAN', 100000, 12, 12.0, 1, 'HUMAN_REVIEW_REQUIRED', 'REQUIRES_HUMAN_REVIEW')
        """, (app_id,))
    conn.close()

    success = record_human_review(
        application_id=app_id,
        reviewer_id="OFFICER-44",
        reviewer_name="Senior Underwriter Jane",
        role="Credit Officer",
        decision="APPROVE",
        findings="Verified physical bank passbook and confirmed stable government employment.",
        conditions="Subject to initial salary credit confirmation."
    )
    assert success is True

    details = get_application_details(app_id)
    assert details["status"] == "APPROVED_BY_AUTHORIZED_LENDER"
    assert len(details["human_reviews"]) > 0
    assert details["human_reviews"][0]["reviewer_name"] == "Senior Underwriter Jane"


def test_fraud_investigation_workflow():
    """Test 10: Fraud case creation and resolution."""
    app_id = "TEST-FRD-APP-001"
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT OR REPLACE INTO applicants (applicant_id, full_name, email, phone, date_of_birth, age, employment_type, monthly_income) VALUES ('AP-FRD', 'Fake Name', 'f@f.org', '111', '1990', 30, 'None', 10000)")
        conn.execute("INSERT OR REPLACE INTO applications (application_id, applicant_id, loan_product, requested_loan_amount, loan_tenure_months, proposed_interest_rate, consent_given, status) VALUES (?, 'AP-FRD', 'PERSONAL_LOAN', 50000, 12, 12, 1, 'RECEIVED')", (app_id,))
    conn.close()

    case_id = create_fraud_case(
        application_id=app_id,
        triggering_flags=["TAMPERED_DOCUMENT", "IDENTITY_MISMATCH"],
        evidence_notes="Uploaded document metadata indicates digital modification.",
        investigator_id="INV-07"
    )
    assert case_id.startswith("FRD-")

    # Resolve fraud case
    resolved = resolve_fraud_case(
        case_id=case_id,
        status="CONFIRMED_FRAUD",
        resolution_notes="Confirmed duplicate identity tampering.",
        investigator_id="INV-07"
    )
    assert resolved is True


def test_complaints_disputes_workflow():
    """Test 11: Opening and resolving an applicant dispute."""
    case_id = create_complaint_case(
        application_id="TEST-DISP-001",
        applicant_name="Mohit Sharma",
        contact_info="mohit@sharma.in",
        category="DISPUTED_CREDIT_INFO",
        priority="HIGH",
        description="Bureau credit score reflects a settled card from 5 years ago that was cleared."
    )
    assert case_id.startswith("DISP-")

    res = resolve_complaint_case(
        case_id=case_id,
        status="RESOLVED",
        resolution_summary="Obtained NOC from issuer; re-scored applicant file.",
        reviewer="Compliance Officer Anita"
    )
    assert res is True
