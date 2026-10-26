"""
Authorized Integration Services and Sandboxes.
Provides interfaces for external services (KYC, Bureau, Banking, E-Sign, LOS, Disbursement, Notification)
with explicit labels clearly distinguishing SIMULATED responses from LIVE integrations.
"""

import time
import uuid
from typing import Dict, Any, Optional
from config.settings import (
    SIMULATED_KYC_MODE,
    SIMULATED_BUREAU_MODE,
    SIMULATED_BANKING_MODE,
    SIMULATED_DISBURSEMENT_MODE,
)
from services.database import get_db_connection


class IntegrationService:
    """Gateway for all external third-party fintech interfaces."""

    @classmethod
    def _log_event(cls, service_name: str, mode: str, summary: str, status: str, duration_ms: float):
        try:
            conn = get_db_connection()
            with conn:
                conn.execute("""
                INSERT INTO integration_events (service_name, mode, request_summary, response_status, duration_ms)
                VALUES (?, ?, ?, ?, ?)
                """, (service_name, mode, summary, status, duration_ms))
            conn.close()
        except Exception:
            pass

    @classmethod
    def verify_identity_kyc(cls, national_id: str, full_name: str) -> Dict[str, Any]:
        """
        Query identity verification service.
        Explicitly marked as SIMULATED in academic prototype.
        """
        t0 = time.time()
        mode = "SIMULATED_MOCK" if SIMULATED_KYC_MODE else "LIVE"

        # Check for synthetic test cases
        if "FRAUD" in national_id.upper() or "STOLEN" in national_id.upper():
            duration_ms = round((time.time() - t0) * 1000, 2)
            cls._log_event("KYC_PROVIDER", mode, f"Verify {national_id}", "FLAGGED_MISMATCH", duration_ms)
            return {
                "verified": False,
                "status": "FLAGGED_MISMATCH",
                "mode": mode,
                "provider": "Academic Synthetic Identity Registry",
                "message": "[SIMULATED NOTICE] Identity record flagged as mismatched or reported lost in synthetic directory.",
                "confidence_score": 0.20
            }

        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("KYC_PROVIDER", mode, f"Verify {national_id}", "VERIFIED_MATCH", duration_ms)
        return {
            "verified": True,
            "status": "VERIFIED_MATCH",
            "mode": mode,
            "provider": "Academic Synthetic Identity Registry",
            "message": "[SIMULATED NOTICE] Synthetic identity verification token issued. Not a real government check.",
            "confidence_score": 0.95
        }

    @classmethod
    def fetch_credit_bureau_score(cls, national_id: str, phone: str) -> Dict[str, Any]:
        """Fetch credit bureau score (e.g. CIBIL/Experian/Equifax mock)."""
        t0 = time.time()
        mode = "SIMULATED_MOCK" if SIMULATED_BUREAU_MODE else "LIVE"

        # Deterministic synthetic score generator based on ID or default
        score = 735
        if "LOW" in national_id.upper() or "DEF" in national_id.upper():
            score = 540

        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("CREDIT_BUREAU", mode, f"Pull bureau for {phone[-4:]}", "SUCCESS", duration_ms)

        return {
            "score": score,
            "bureau_name": "Synthetic Credit Bureau Sandbox",
            "mode": mode,
            "inquiries_last_6m": 2,
            "active_tradelines": 3,
            "delinquencies": 0 if score > 600 else 2,
            "message": "[SIMULATED NOTICE] Credit bureau report generated from academic sandbox profile."
        }

    @classmethod
    def verify_bank_statement_aggregator(cls, account_number_masked: str) -> Dict[str, Any]:
        """Account Aggregator / Open Banking verification."""
        t0 = time.time()
        mode = "SIMULATED_MOCK" if SIMULATED_BANKING_MODE else "LIVE"

        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("ACCOUNT_AGGREGATOR", mode, "Verify statement flow", "SUCCESS", duration_ms)

        return {
            "verified": True,
            "mode": mode,
            "average_monthly_balance": 34500.0,
            "salary_credits_detected": True,
            "bounces_last_90d": 0,
            "message": "[SIMULATED NOTICE] Open banking sandbox transaction baseline verified."
        }

    @classmethod
    def request_digital_signature(cls, application_id: str, applicant_email: str) -> Dict[str, Any]:
        """E-Signature initiation (Aadhaar eSign / DocuSign sandbox)."""
        t0 = time.time()
        envelope_id = f"ESIGN-{uuid.uuid4().hex[:8].upper()}"
        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("ESIGN_SERVICE", "SIMULATED_MOCK", f"E-sign for {application_id}", "DISPATCHED", duration_ms)

        return {
            "envelope_id": envelope_id,
            "status": "PENDING_APPLICANT_SIGNATURE",
            "mode": "SIMULATED_MOCK",
            "signing_url": f"https://mock-esign.academic-fintech.local/sign/{envelope_id}",
            "message": "[SIMULATED NOTICE] Digital signature workflow initialized in sandbox mode."
        }

    @classmethod
    def transmit_to_loan_origination_system(cls, application_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transmits pre-screened file to authorized core banking LOS."""
        t0 = time.time()
        los_id = f"LOS-{uuid.uuid4().hex[:8].upper()}"
        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("CORE_LOS", "SIMULATED_MOCK", f"Ingest {application_id}", "ACKNOWLEDGED", duration_ms)

        return {
            "los_reference_id": los_id,
            "status": "INGESTED_FOR_FINAL_SANCTION",
            "mode": "SIMULATED_MOCK",
            "message": "[SIMULATED NOTICE] Packet queued in mock Loan Origination System for sanction committee review."
        }

    @classmethod
    def initiate_disbursement(cls, application_id: str, amount: float) -> Dict[str, Any]:
        """
        Disbursement endpoint.
        NOTE: Real disbursements are strictly prevented in this academic prototype.
        """
        t0 = time.time()
        tx_id = f"SIM-TX-{uuid.uuid4().hex[:10].upper()}"
        duration_ms = round((time.time() - t0) * 1000, 2)
        cls._log_event("PAYMENT_GATEWAY", "SIMULATED_MOCK", f"Disburse {amount} for {application_id}", "SIMULATED_ONLY", duration_ms)

        return {
            "disbursement_id": tx_id,
            "amount": amount,
            "status": "SIMULATED_RECORD_ONLY",
            "mode": "SIMULATED_MOCK",
            "warning": "Real money transfers are strictly disabled in this educational prototype. No funds were debited or transferred."
        }
