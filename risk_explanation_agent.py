"""
Agent 6: Risk Explanation and Recommendation Agent.
Synthesizes outputs from Agents 2-5, compiles an evidence trail of positive and negative factors,
applies the Safe Decision Policy, and drafts an underwriter summary for human credit officers.
Supports distinct logic for Personal Loans and Education Loans.
"""

from typing import Dict, Any, List, Optional
from models.schemas import RiskExplanationResult, PreliminaryOutcome
from services.decision_policy import SafeDecisionPolicy
from config.settings import ACADEMIC_PROTOTYPE_DISCLAIMER


class RiskExplanationAgent:
    """Agent 6: Generates traceable, evidence-backed explanations and safe routing outcomes."""

    def generate_recommendation(
        self,
        applicant_data: Dict[str, Any],
        validation_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        rules_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        has_open_dispute: bool = False,
        has_fraud_flag: bool = False,
        has_duplicate_flag: bool = False
    ) -> RiskExplanationResult:
        positive_factors: List[str] = []
        negative_factors: List[str] = []

        loan_product = applicant_data.get("loan_product", "PERSONAL_LOAN")

        # 1. Analyze Validation Factors
        if validation_data.get("is_valid", False):
            positive_factors.append("All mandatory application fields and initial document headers are present and valid.")
        else:
            errors = validation_data.get("blocking_errors", [])
            negative_factors.extend([f"Data Error: {e}" for e in errors])

        inconsistencies = validation_data.get("inconsistency_flags", [])
        if inconsistencies:
            negative_factors.extend([f"Data Conflict: {inc}" for inc in inconsistencies])

        duplicates = validation_data.get("duplicate_flags", [])
        if duplicates:
            negative_factors.extend([f"Security Flag: {d}" for d in duplicates])

        # 2. Analyze Financial Factors
        dti = financial_data.get("dti_ratio", 0.0)
        net_disposable = financial_data.get("net_disposable_income", 0.0)
        emi = financial_data.get("monthly_emi", 0.0)
        income = float(applicant_data.get("monthly_income", 0.0))
        coapp_income = float(applicant_data.get("co_applicant_income", 0.0))

        if loan_product == "EDUCATION_LOAN":
            if coapp_income > 0:
                positive_factors.append(f"Parent/co-applicant demonstrates verified monthly income of INR {coapp_income:,.2f}.")
            admission_st = applicant_data.get("admission_status")
            if admission_st == "Confirmed Admission":
                positive_factors.append(f"Institution admission status confirmed ({applicant_data.get('university_name', '')}).")
            if dti <= 0.50 and coapp_income > 0:
                positive_factors.append(f"Co-applicant debt service obligation ratio {round(dti*100, 1)}% is comfortable.")
            elif dti > 0.65:
                negative_factors.append(f"Co-applicant obligation-to-income ratio ({round(dti*100, 1)}%) exceeds 65% ceiling.")
        else:
            if dti <= 0.40 and income > 0:
                positive_factors.append(f"Comfortable debt-to-income ratio of {round(dti*100, 1)}% (< 40% threshold).")
            elif dti <= 0.50:
                positive_factors.append(f"Moderate debt-to-income ratio of {round(dti*100, 1)}% within standard limits.")
            elif income > 0:
                negative_factors.append(f"Elevated debt-to-income ratio of {round(dti*100, 1)}%, indicating debt servicing pressure.")

            if net_disposable > (income * 0.40) and income > 0:
                positive_factors.append(f"Strong disposable monthly buffer of INR {net_disposable:,.2f} remaining after all obligations.")

        # 3. Analyze Rules Factors
        rules_passed = rules_data.get("rules_passed", 0)
        rules_failed = rules_data.get("rules_failed", 0)
        rule_items = rules_data.get("rule_items", [])

        if rules_failed == 0 and rules_passed > 0:
            positive_factors.append(f"Passed all {rules_passed} evaluated institutional lending policy rules.")
        else:
            for item in rule_items:
                if item.get("result") == "FAIL":
                    negative_factors.append(f"Rule Failure: {item.get('name')} - {item.get('explanation')}")

        # 4. Analyze Credit Risk ML Factors
        score = applicant_data.get("credit_score")
        if score and score >= 750:
            positive_factors.append(f"Credit bureau score of {score} is in the prime range.")
        elif score and score >= 650:
            positive_factors.append(f"Fair credit bureau score of {score}.")
        elif score:
            negative_factors.append(f"Sub-optimal credit bureau score of {score} (< 650).")

        risk_cat = risk_data.get("risk_category")
        risk_score = risk_data.get("risk_score")
        if risk_cat == "LOW":
            positive_factors.append(f"Predictive risk model indicates LOW default probability ({round((risk_score or 0.1)*100, 1)}%).")
        elif risk_cat == "HIGH":
            negative_factors.append(f"Predictive risk model indicates HIGH default probability ({round((risk_score or 0.8)*100, 1)}%).")

        # 5. Apply Safe Decision Policy Engine
        prelim_outcome, status, escalation_flags, evidence_trail = SafeDecisionPolicy.evaluate_workflow_progression(
            validation_data=validation_data,
            financial_data=financial_data,
            rules_data=rules_data,
            risk_data=risk_data,
            has_open_dispute=has_open_dispute,
            has_fraud_flag=has_fraud_flag,
            has_duplicate_flag=has_duplicate_flag
        )

        # 6. Draft Underwriter Summary
        pause_reason = None
        human_summary = None

        if prelim_outcome == PreliminaryOutcome.PROCEED_TO_NEXT_STAGE:
            human_summary = (
                "STRAIGHTFORWARD PRE-SCREENING: Applicant satisfies baseline identity, income, policy, "
                "and risk criteria. Recommended to proceed to next origination stage (e.g. formal sanction committee or KYC completion)."
            )
        elif prelim_outcome == PreliminaryOutcome.MORE_INFORMATION_REQUIRED:
            pause_reason = "Mandatory applicant fields or required verification documents are incomplete."
            human_summary = (
                f"ACTION PAUSED: Missing information detected. A notification has been queued for applicant clarification. "
                f"Escalation details: {'; '.join(escalation_flags)}"
            )
        elif prelim_outcome == PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION:
            pause_reason = "Application placed on hold due to an active dispute or pending verification."
            human_summary = f"HELD FOR INVESTIGATION: {'; '.join(escalation_flags)}"
        else: # REQUIRES_HUMAN_REVIEW
            pause_reason = "Application triggered policy exceptions, elevated risk, or data inconsistencies."
            human_summary = (
                f"CREDIT OFFICER REVIEW MANDATED: Automated continuation was halted. "
                f"Primary escalation reasons: {'; '.join(escalation_flags)}"
            )

        return RiskExplanationResult(
            loan_product=loan_product,
            preliminary_outcome=prelim_outcome,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            evidence_trail=evidence_trail,
            human_review_summary=human_summary,
            pause_reason=pause_reason,
            escalation_flags=escalation_flags,
            disclaimer=ACADEMIC_PROTOTYPE_DISCLAIMER
        )
