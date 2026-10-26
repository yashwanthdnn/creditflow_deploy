"""
Agent 3: Financial Analysis Agent.
Performs deterministic financial computations: standard reducing-balance EMI,
debt-to-income (DTI) leverage, APR, upfront deductions, education cost reconciliation,
and moratorium capitalization without product leakage.
"""

from typing import Dict, Any, List
from models.schemas import FinancialAnalysisResult, ExpenseReconciliation
from config.settings import DEFAULT_ANNUAL_INTEREST_RATE, MAX_PERMITTED_DTI, HIGH_RISK_DTI_THRESHOLD
from services.financial_engine import FinancialEngine


class FinancialAnalysisAgent:
    """Agent 3: Responsible for mathematical financial obligations and capacity evaluation."""

    def __init__(self, default_annual_rate: float = DEFAULT_ANNUAL_INTEREST_RATE):
        self.default_annual_rate = default_annual_rate

    def calculate_emi(self, principal: float, annual_rate_pct: float, tenure_months: int) -> float:
        """Call core FinancialEngine reducing-balance EMI."""
        return FinancialEngine.calculate_emi(principal, annual_rate_pct, tenure_months)

    def analyze(self, applicant_data: Dict[str, Any]) -> FinancialAnalysisResult:
        principal = float(applicant_data.get("requested_loan_amount", 0.0))
        tenure_months = int(applicant_data.get("loan_tenure_months", 0))
        annual_rate = float(applicant_data.get("proposed_interest_rate", self.default_annual_rate))
        loan_product = applicant_data.get("loan_product", "PERSONAL_LOAN")

        student_income = float(applicant_data.get("monthly_income", 0.0))
        coapp_income = float(applicant_data.get("co_applicant_income", 0.0))
        student_existing_obligations = float(applicant_data.get("existing_monthly_obligations", 0.0))
        coapp_existing_obligations = float(applicant_data.get("co_applicant_existing_emi", 0.0))

        warnings: List[str] = []
        is_reliable = True

        if principal <= 0:
            warnings.append("Requested loan amount is zero or missing.")
            is_reliable = False
        if tenure_months <= 0:
            warnings.append("Loan tenure in months is invalid.")
            is_reliable = False

        # In Education Loan, student income can be 0. We evaluate affordability on co-applicant income.
        if loan_product == "EDUCATION_LOAN":
            effective_income = coapp_income
            total_existing_obligations = round(student_existing_obligations + coapp_existing_obligations, 2)
            if effective_income <= 0 and principal > 400000.0:
                warnings.append("Co-applicant income is missing; cannot reliably compute debt service ratio for education loan > INR 4 Lakhs.")
                is_reliable = False
        else:
            effective_income = student_income
            total_existing_obligations = student_existing_obligations
            if effective_income <= 0:
                warnings.append("Monthly take-home income is zero or missing for Personal Loan.")
                is_reliable = False

        # Standard reducing-balance EMI
        monthly_emi = self.calculate_emi(principal, annual_rate, tenure_months) if is_reliable else 0.0
        total_monthly_obligations = round(total_existing_obligations + monthly_emi, 2)

        # Ratios
        if effective_income > 0:
            dti_ratio = round(total_monthly_obligations / effective_income, 4)
            annual_income = effective_income * 12.0
            loan_to_annual_income = round(principal / annual_income, 2)
            net_disposable_income = round(effective_income - total_monthly_obligations, 2)
        else:
            dti_ratio = 0.0
            loan_to_annual_income = 0.0
            net_disposable_income = 0.0

        # Assess debt stress indicators
        indicators: Dict[str, Any] = {}
        if dti_ratio > MAX_PERMITTED_DTI:
            indicators["dti_stress"] = "CRITICAL_EXPOSURE"
            warnings.append(
                f"Debt-to-Income ratio ({round(dti_ratio*100, 1)}%) exceeds policy maximum of {int(MAX_PERMITTED_DTI*100)}%."
            )
        elif dti_ratio > HIGH_RISK_DTI_THRESHOLD:
            indicators["dti_stress"] = "ELEVATED_RISK"
            warnings.append(
                f"Debt-to-Income ratio ({round(dti_ratio*100, 1)}%) is elevated (> {int(HIGH_RISK_DTI_THRESHOLD*100)}%)."
            )
        else:
            indicators["dti_stress"] = "COMFORTABLE"

        # Upfront deductions and APR
        net_disbursed, total_upfront, upfront_breakdown = FinancialEngine.calculate_net_disbursement(principal)
        apr_pct = FinancialEngine.calculate_apr(principal, net_disbursed, monthly_emi, tenure_months)

        # Education-specific calculations
        edu_recon_dict = None
        edu_moratorium_dict = None
        if loan_product == "EDUCATION_LOAN":
            edu_recon = FinancialEngine.reconcile_education_costs(
                tuition=float(applicant_data.get("tuition_fees", 0.0)),
                admission_reg=float(applicant_data.get("admission_reg_fees", 0.0)),
                exam_fees=float(applicant_data.get("examination_fees", 0.0)),
                hostel=float(applicant_data.get("hostel_living_cost", 0.0)),
                books_equipment=float(applicant_data.get("books_equipment_cost", 0.0)),
                travel_living=float(applicant_data.get("travel_living_cost", 0.0)),
                confirmed_scholarship=float(applicant_data.get("confirmed_scholarship", 0.0)),
                unconfirmed_scholarship=float(applicant_data.get("unconfirmed_scholarship", 0.0)),
                other_funding=float(applicant_data.get("other_funding", 0.0)),
                student_contribution=float(applicant_data.get("student_contribution", 0.0))
            )
            edu_recon_dict = edu_recon.model_dump()

            moratorium_months = int(applicant_data.get("moratorium_months") or 36)
            edu_moratorium_dict = FinancialEngine.calculate_education_moratorium_and_repayment(
                principal=principal,
                annual_rate_pct=annual_rate,
                moratorium_months=moratorium_months,
                repayment_tenure_months=tenure_months
            )
            indicators["interest_subsidy_status"] = "Not assessed — Eligibility pending verification"

        assumptions = {
            "interest_calculation_type": "Reducing-Balance Monthly Compounding",
            "annual_nominal_interest_rate_pct": annual_rate,
            "monthly_effective_rate_pct": round((annual_rate / 12.0), 4),
            "max_permitted_dti_threshold": MAX_PERMITTED_DTI,
            "high_risk_dti_threshold": HIGH_RISK_DTI_THRESHOLD,
            "zero_interest_handled": annual_rate == 0.0,
            "apr_percentage": apr_pct,
            "net_disbursed_amount": net_disbursed,
            "total_upfront_deductions": total_upfront,
            "education_cost_reconciliation": edu_recon_dict,
            "education_moratorium": edu_moratorium_dict,
            "engine_version": "FinancialEngine-v2.4"
        }

        explanation = (
            f"Monthly EMI of INR {monthly_emi:,.2f} computed using reducing-balance formula at {annual_rate}% annual rate "
            f"over {tenure_months} months. Combined monthly debt obligations: INR {total_monthly_obligations:,.2f}, "
            f"representing {round(dti_ratio * 100, 1)}% of effective monthly income (INR {effective_income:,.2f})."
        )

        return FinancialAnalysisResult(
            loan_product=loan_product,
            monthly_emi=monthly_emi,
            existing_obligations=total_existing_obligations,
            total_monthly_obligations=total_monthly_obligations,
            dti_ratio=dti_ratio,
            loan_to_annual_income=loan_to_annual_income,
            net_disposable_income=net_disposable_income,
            upfront_charges=total_upfront,
            net_disbursement=net_disbursed,
            annual_percentage_rate=apr_pct,
            risk_indicators=indicators,
            repayment_indicators={k: str(v) for k, v in indicators.items()},
            is_reliable=is_reliable,
            calculation_assumptions=assumptions,
            assumptions=assumptions,
            calculation_explanation=explanation,
            warnings=warnings
        )
