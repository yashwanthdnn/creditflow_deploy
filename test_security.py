"""
Security, Privacy, and Access Control Tests.
Tests parameterized SQL defense against SQL injection, data minimization,
and external mock integration error handling.
"""

from services.database import list_applications, get_db_connection
from services.integration_service import IntegrationService


def test_sql_injection_defense_in_search():
    """Test 18: Malicious SQL injection payloads in search query are neutralized."""
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE applications; --",
        "admin'--",
        "1 UNION SELECT null, null, null--"
    ]
    for term in malicious_inputs:
        # Should execute safely via parameterized query without throwing or dropping tables
        res = list_applications(search=term)
        assert isinstance(res, list)

    # Verify applications table still exists
    conn = get_db_connection()
    row = conn.execute("SELECT COUNT(*) FROM applications").fetchone()
    assert row is not None
    conn.close()


def test_data_minimization_check():
    """Verify schema does not contain passwords, OTPs, or payment card numbers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = [row[1].lower() for row in cursor.execute("PRAGMA table_info(applicants)").fetchall()]
    conn.close()

    prohibited_fields = ["password", "otp", "pin", "cvv", "credit_card_number", "pan_raw"]
    for field in prohibited_fields:
        assert field not in columns, f"Prohibited sensitive field '{field}' detected in schema!"


def test_integration_mock_graceful_timeout_handling():
    """Test 12: External integration returns structured simulated status without crashing."""
    res = IntegrationService.verify_identity_kyc("TEST-FRAUD-ID", "Test Name")
    assert res["status"] == "FLAGGED_MISMATCH"
    assert res["mode"] == "SIMULATED_MOCK"
    assert "SIMULATED" in res["message"]

    bureau_res = IntegrationService.fetch_credit_bureau_score("DEF-ID", "9999999999")
    assert bureau_res["mode"] == "SIMULATED_MOCK"
    assert bureau_res["score"] < 600

    disb_res = IntegrationService.initiate_disbursement("APP-001", 50000.0)
    assert disb_res["status"] == "SIMULATED_RECORD_ONLY"
    assert "Real money transfers are strictly disabled" in disb_res["warning"]
