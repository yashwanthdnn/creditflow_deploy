"""
Agent 5: Credit Risk Agent.
Loads versioned ML model pipeline, executes statistical inference,
estimates probability of default, and reports model versioning & limitations.
Supports Education Loan co-applicant profile adaptation.
"""

from typing import Dict, Any, Optional
from models.schemas import CreditRiskResult
from ml.predict import CreditRiskPredictor


class CreditRiskAgent:
    """Agent 5: Machine Learning decision-support scoring for default probability."""

    def assess_risk(
        self,
        applicant_data: Dict[str, Any],
        financial_data: Optional[Dict[str, Any]] = None
    ) -> CreditRiskResult:
        """
        Execute risk assessment by unifying applicant profile and financial metrics.
        """
        payload = dict(applicant_data)
        loan_product = payload.get("loan_product", "PERSONAL_LOAN")

        # Merge financial ratios computed by Agent 3
        if financial_data:
            payload["dti_ratio"] = financial_data.get("dti_ratio", 0.0)
            if "requested_loan_amount" not in payload:
                payload["requested_loan_amount"] = financial_data.get("requested_loan_amount", 0.0)

        # In Education Loan, if student income is 0, use co-applicant income for modeling
        added_warnings = []
        if loan_product == "EDUCATION_LOAN":
            student_inc = float(payload.get("monthly_income") or 0.0)
            coapp_inc = float(payload.get("co_applicant_income") or 0.0)
            if student_inc <= 0 and coapp_inc > 0:
                payload["monthly_income"] = coapp_inc
                added_warnings.append("Student has zero pre-course income; ML risk assessed using co-applicant monthly earnings.")

        # Call ML prediction engine
        res_dict = CreditRiskPredictor.predict_risk(payload)

        all_warnings = res_dict.get("warnings", []) + added_warnings

        return CreditRiskResult(
            risk_score=res_dict.get("risk_score"),
            risk_category=res_dict.get("risk_category", "UNCERTAIN"),
            model_version=res_dict.get("model_version", "v1.2-academic"),
            model_name=res_dict.get("model_name", "RandomForestClassifier"),
            features_used=res_dict.get("features_used", []),
            inference_timestamp=res_dict.get("inference_timestamp", ""),
            is_prediction_reliable=res_dict.get("is_prediction_reliable", True),
            limitations=res_dict.get("limitations", []),
            warnings=all_warnings,
            explanation_notes=res_dict.get("explanation_notes", "")
        )
