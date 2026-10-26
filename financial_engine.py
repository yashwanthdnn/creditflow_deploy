"""
Financial Engine for CreditFlow AI:
Deterministic amortization, APR calculations, reducing-balance EMI,
Education Loan moratorium/capitalization, and expense reconciliation.
"""

from typing import Dict, Any, List, Tuple, Optional
from models.schemas import ExpenseReconciliation, AmortizationScheduleRow


class FinancialEngine:
    """Core mathematical engine for loan repayments, APR, and student cost reconciliation."""

    @staticmethod
    def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
        """
        Standard reducing-balance monthly EMI formula.
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        Zero-rate handled as P / n.
        """
        if principal <= 0 or tenure_months <= 0:
            return 0.0

        if annual_rate_pct <= 0.0:
            return round(principal / tenure_months, 2)

        monthly_rate = (annual_rate_pct / 100.0) / 12.0
        factor = (1.0 + monthly_rate) ** tenure_months
        emi = principal * monthly_rate * factor / (factor - 1.0)
        return round(float(emi), 2)

    @staticmethod
    def calculate_net_disbursement(
        principal: float,
        processing_fee_pct: float = 1.0,
        documentation_fee: float = 750.0,
        stamp_duty: float = 500.0,
        gst_pct: float = 18.0
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Calculate upfront deductions and net disbursed amount.
        Processing fee GST applied on fee portion.
        """
        if principal <= 0:
            return 0.0, 0.0, {}

        proc_fee = round(principal * (processing_fee_pct / 100.0), 2)
        proc_gst = round(proc_fee * (gst_pct / 100.0), 2)
        total_upfront = round(proc_fee + proc_gst + documentation_fee + stamp_duty, 2)
        net_disbursed = round(principal - total_upfront, 2)

        itemized = {
            "processing_fee": proc_fee,
            "processing_fee_gst": proc_gst,
            "documentation_charges": documentation_fee,
            "stamp_duty": stamp_duty,
            "total_upfront_deductions": total_upfront
        }
        return net_disbursed, total_upfront, itemized

    @staticmethod
    def calculate_apr(
        principal: float,
        net_disbursement: float,
        monthly_emi: float,
        tenure_months: int
    ) -> Optional[float]:
        """
        Calculate Annual Percentage Rate (APR) using Newton-Raphson IRR method.
        Solves: NetDisbursement = sum_{t=1}^n (EMI / (1 + r)^t)
        Annualized APR = monthly_irr * 12 * 100
        """
        if net_disbursement <= 0 or monthly_emi <= 0 or tenure_months <= 0:
            return None

        # Solve for monthly IRR using Newton-Raphson
        # f(r) = -NetDisbursement + sum(EMI / (1+r)^t) = 0
        r = 0.01  # initial guess 1% monthly
        for _ in range(50):
            # Calculate f(r) and f'(r)
            f_val = -net_disbursement
            f_prime = 0.0
            for t in range(1, tenure_months + 1):
                disc = (1.0 + r) ** t
                f_val += monthly_emi / disc
                f_prime -= (t * monthly_emi) / ((1.0 + r) ** (t + 1))

            if abs(f_val) < 1e-6:
                break
            if abs(f_prime) < 1e-12:
                break
            diff = f_val / f_prime
            r = r - diff
            if r <= -0.99:
                r = 0.0001

        apr_annual_pct = round(r * 12.0 * 100.0, 2)
        return apr_annual_pct

    @staticmethod
    def generate_amortization_schedule(
        principal: float,
        annual_rate_pct: float,
        tenure_months: int,
        max_rows: int = 360
    ) -> List[AmortizationScheduleRow]:
        """Generate monthly amortization breakdown."""
        schedule = []
        if principal <= 0 or tenure_months <= 0:
            return schedule

        emi = FinancialEngine.calculate_emi(principal, annual_rate_pct, tenure_months)
        monthly_rate = (annual_rate_pct / 100.0) / 12.0
        balance = principal

        for m in range(1, min(tenure_months, max_rows) + 1):
            opening = balance
            interest = round(opening * monthly_rate, 2)
            principal_comp = round(emi - interest, 2)
            if m == tenure_months:
                principal_comp = opening
                closing = 0.0
            else:
                closing = round(max(0.0, opening - principal_comp), 2)

            balance = closing
            schedule.append(AmortizationScheduleRow(
                month=m,
                opening_balance=opening,
                monthly_payment=emi,
                principal_component=principal_comp,
                interest_component=interest,
                closing_balance=closing
            ))
        return schedule

    @staticmethod
    def reconcile_education_costs(
        tuition: float,
        admission_reg: float,
        exam_fees: float,
        hostel: float,
        books_equipment: float,
        travel_living: float,
        confirmed_scholarship: float = 0.0,
        unconfirmed_scholarship: float = 0.0,
        other_funding: float = 0.0,
        student_contribution: float = 0.0
    ) -> ExpenseReconciliation:
        """
        Reconcile Education Loan funding requirement (Section A.2).
        Eligible = Tuition + Admission + Exam + Hostel + Books + Travel
        Indicative Financing = Eligible - Confirmed Scholarships - Other Funding - Student Contribution
        NOTE: Unconfirmed scholarships are EXCLUDED from automatic deduction.
        """
        total_eligible = round(
            tuition + admission_reg + exam_fees + hostel + books_equipment + travel_living, 2
        )
        total_deductions = round(confirmed_scholarship + other_funding + student_contribution, 2)
        indicative_req = round(max(0.0, total_eligible - total_deductions), 2)

        return ExpenseReconciliation(
            total_declared_eligible_expenses=total_eligible,
            confirmed_scholarships=confirmed_scholarship,
            unconfirmed_scholarships=unconfirmed_scholarship,
            other_funding_sources=other_funding,
            student_contribution=student_contribution,
            indicative_financing_requirement=indicative_req,
            is_provisional=True
        )

    @staticmethod
    def calculate_education_moratorium_and_repayment(
        principal: float,
        annual_rate_pct: float,
        moratorium_months: int,
        repayment_tenure_months: int
    ) -> Dict[str, Any]:
        """
        Calculate Education Loan study-period interest, capitalization, and post-moratorium EMI.
        Simple interest accrues during course + moratorium.
        Capitalized principal at repayment commencement = P + StudyPeriodInterest.
        Post-moratorium EMI computed on capitalized balance.
        """
        if principal <= 0 or repayment_tenure_months <= 0:
            return {
                "study_period_interest": 0.0,
                "capitalized_principal": 0.0,
                "post_moratorium_monthly_emi": 0.0,
                "moratorium_months": moratorium_months
            }

        # Simple interest during study + grace period
        rate_fraction = annual_rate_pct / 100.0
        time_years = moratorium_months / 12.0
        study_interest = round(principal * rate_fraction * time_years, 2)
        capitalized_principal = round(principal + study_interest, 2)

        # Repayment EMI on capitalized balance
        post_moratorium_emi = FinancialEngine.calculate_emi(
            principal=capitalized_principal,
            annual_rate_pct=annual_rate_pct,
            tenure_months=repayment_tenure_months
        )

        return {
            "study_period_interest": study_interest,
            "capitalized_principal": capitalized_principal,
            "post_moratorium_monthly_emi": post_moratorium_emi,
            "moratorium_months": moratorium_months,
            "repayment_tenure_months": repayment_tenure_months
        }

    @staticmethod
    def run_what_if_scenario(
        principal: float,
        annual_rate_pct: float,
        tenure_months: int,
        existing_obligations: float,
        monthly_income: float
    ) -> Dict[str, Any]:
        """Perform instant recalculation for What-If parameter modifications."""
        emi = FinancialEngine.calculate_emi(principal, annual_rate_pct, tenure_months)
        total_monthly = round(existing_obligations + emi, 2)
        dti = round(total_monthly / monthly_income, 4) if monthly_income > 0 else 0.0
        total_repayment = round(emi * tenure_months, 2)
        total_interest = round(max(0.0, total_repayment - principal), 2)
        net_disposable = round(monthly_income - total_monthly, 2) if monthly_income > 0 else 0.0

        return {
            "principal": principal,
            "annual_rate_pct": annual_rate_pct,
            "tenure_months": tenure_months,
            "monthly_emi": emi,
            "total_monthly_obligations": total_monthly,
            "dti_ratio": dti,
            "total_scheduled_repayment": total_repayment,
            "total_scheduled_interest": total_interest,
            "net_disposable_income": net_disposable
        }
