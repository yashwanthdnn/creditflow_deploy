"""
Maximum Safe Automation Policy Engine.
Enforces safe progression, escalation boundaries, fraud triggers, and human oversight.
"""

from typing import Dict, Any, List, Tuple
from models.schemas import PreliminaryOutcome, ApplicationStatus


class SafeDecisionPolicy:
    """
    Central gatekeeper enforcing the Primary Principle:
    Automate routine verified tasks safely; escalate exceptions, conflicts,
    disputes, fraud signals, or missing data. Never force every case through auto processing.
    """

    @staticmethod
    def evaluate_workflow_progression(
        validation_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        rules_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        has_open_dispute: bool = False,
        has_fraud_flag: bool = False,
        has_duplicate_flag: bool = False
    ) -> Tuple[PreliminaryOutcome, ApplicationStatus, List[str], List[str]]:
        """
        Evaluate all inputs and determine the safe preliminary outcome and workflow status.
        Returns:
            (PreliminaryOutcome, ApplicationStatus, escalation_flags, evidence_trail)
        """
        escalation_flags: List[str] = []
        evidence_trail: List[str] = []

        # 1. Dispute / Complaint Override
        if has_open_dispute:
            escalation_flags.append("ACTIVE_APPLICANT_DISPUTE: An open dispute/grievance requires resolution prior to progression.")
            evidence_trail.append("Assessment paused due to an active legal/applicant dispute ticket.")
            return PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION, ApplicationStatus.DISPUTED, escalation_flags, evidence_trail

        # 2. Fraud & Security Flag Override
        if has_fraud_flag or has_duplicate_flag:
            if has_duplicate_flag:
                escalation_flags.append("POTENTIAL_DUPLICATE_APPLICATION: Matching national ID or identity records detected.")
            if has_fraud_flag:
                escalation_flags.append("SUSPECTED_FRAUD_INDICATOR: Identity/income mismatch or suspicious document pattern detected.")
            evidence_trail.append("Automatic workflow halted: security/fraud investigation case created.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.ON_HOLD, escalation_flags, evidence_trail

        # 3. Missing Mandatory Information or Blocking Validation Errors
        blocking_errors = validation_data.get("blocking_errors", [])
        missing_fields = validation_data.get("missing_fields", [])
        inconsistencies = validation_data.get("inconsistency_flags", [])
        rec_action = validation_data.get("recommended_action")

        if inconsistencies:
            escalation_flags.extend([f"INCONSISTENCY: {inc}" for inc in inconsistencies])
            evidence_trail.append("Form data directly conflicts with verified document extraction.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        if not validation_data.get("is_valid", True) or missing_fields or blocking_errors or rec_action == "MORE_INFORMATION_REQUIRED":
            escalation_flags.extend([f"MISSING/INVALID: {err}" for err in (blocking_errors + missing_fields)])
            evidence_trail.append("Application paused awaiting applicant submission of required fields or documents.")
            return PreliminaryOutcome.MORE_INFORMATION_REQUIRED, ApplicationStatus.MORE_INFORMATION_REQUIRED, escalation_flags, evidence_trail

        # 4. Mandatory Rule Failures (Eligibility & Rules)
        rule_items = rules_data.get("rule_items", [])
        blocking_rule_failures = [
            r for r in rule_items
            if r.get("result") == "FAIL" and r.get("severity") == "BLOCKING"
        ]
        warning_rule_failures = [
            r for r in rule_items
            if r.get("result") == "FAIL" and r.get("severity") == "WARNING"
        ]

        if blocking_rule_failures:
            for r in blocking_rule_failures:
                escalation_flags.append(f"BLOCKING_RULE_FAILED: {r.get('name')} - {r.get('explanation')}")
            evidence_trail.append("Mandatory product eligibility rule criteria not satisfied.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        # 5. Financial Stress & Debt Ceiling Check
        dti = financial_data.get("dti_ratio", 0.0)
        if dti > 0.55:
            escalation_flags.append(f"HIGH_DTI_EXPOSURE: Projected DTI ({round(dti*100, 1)}%) exceeds maximum safe ceiling of 55%.")
            evidence_trail.append("Financial leverage indicates significant debt burden requiring underwriter review.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        if not financial_data.get("is_reliable", True):
            escalation_flags.append("UNRELIABLE_FINANCIAL_INPUTS: Financial inputs could not be computed deterministically.")
            evidence_trail.append("Financial analysis flagged implausible or zero-income parameters.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        # 6. Credit Risk ML Model Outcome Check
        risk_category = risk_data.get("risk_category", "UNCERTAIN")
        risk_score = risk_data.get("risk_score")

        if risk_category == "HIGH":
            escalation_flags.append(f"HIGH_DEFAULT_PROBABILITY: Model estimated default risk at {round((risk_score or 0.0)*100, 1)}%.")
            evidence_trail.append("Predictive model assigned HIGH risk category based on credit history and debt ratios.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        if not risk_data.get("is_prediction_reliable", True):
            escalation_flags.append("MODEL_INPUT_WARNING: Inference executed with out-of-range or demonstration model parameters.")
            evidence_trail.append("Model output is advisory only; requires human validation.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        # 7. Warning-level Rules Review
        if warning_rule_failures or rules_data.get("requires_human_review"):
            for r in warning_rule_failures:
                escalation_flags.append(f"POLICY_EXCEPTION: {r.get('name')} - {r.get('explanation')}")
            evidence_trail.append("Soft rule warning triggered; escalated to credit officer review queue.")
            return PreliminaryOutcome.REQUIRES_HUMAN_REVIEW, ApplicationStatus.HUMAN_REVIEW_REQUIRED, escalation_flags, evidence_trail

        # 8. All Checks Clear: Straightforward Pre-Screening Pass
        evidence_trail.append("Applicant details complete, document validation verified, eligibility rules passed, DTI within safe limit, and risk model indicates acceptable profile.")
        return PreliminaryOutcome.PROCEED_TO_NEXT_STAGE, ApplicationStatus.PRE_SCREENING_COMPLETED, escalation_flags, evidence_trail
