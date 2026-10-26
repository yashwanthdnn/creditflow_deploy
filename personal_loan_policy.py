"""
Personal Loan Policy and Document Checklist Service:
Encapsulates lender policies, required documentation periods, and financial thresholds
strictly dedicated to the Personal Loan product without cross-contamination.
"""

from typing import Dict, Any, List
from models.schemas import DocumentRequirementItem, DocumentStatus


class PersonalLoanPolicy:
    """Dedicated policy engine and document checklist for Unsecured Personal Loans."""

    POLICY_VERSION = "v2.4-personal"

    DOCUMENT_REQUIREMENTS: List[DocumentRequirementItem] = [
        DocumentRequirementItem(
            requirement_id="REQ-PL-ID",
            document_name="Government Identity Proof",
            reason_requested="Legal KYC identity establishment (Passport / PAN / National ID)",
            source_policy_reference="RBI Master Direction - KYC Direction, 2016 (Updated 2023)",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="OCR entity extraction & synthetic KYC token match"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-PL-ADDR",
            document_name="Proof of Address",
            reason_requested="Verification of permanent and current physical residence",
            source_policy_reference="Institutional Credit Policy Section 3.2",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="Utility bill / Aadhaar masked address verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-PL-PHOTO",
            document_name="Applicant Photograph",
            reason_requested="Recent visual applicant identification record",
            source_policy_reference="Institutional Credit Policy Section 3.4",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".jpg", ".jpeg", ".png"],
            verification_method="Format, dimensions, and image integrity verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-PL-SALARY-SLIPS",
            document_name="Salary Slips (Last 3 Months)",
            reason_requested="Proof of active salaried employment and net monthly take-home earnings",
            source_policy_reference="Institutional Underwriting Guidelines 2024",
            status_type="Mandatory",
            applicable_stage="FINANCIAL_ANALYSIS",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="PDF text parse: verify employer name, net pay, and deductions"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-PL-BANK-STMT",
            document_name="Bank Account Statement (Last 6 Months)",
            reason_requested="Verifies regular salary credit inflows, average balance, and absence of cheque bounces",
            source_policy_reference="Institutional Underwriting Guidelines 2024",
            status_type="Mandatory",
            applicable_stage="FINANCIAL_ANALYSIS",
            accepted_formats=[".pdf"],
            verification_method="Account aggregator / bank statement transaction reconciliation"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-PL-FORM16",
            document_name="Form 16 / Income Tax Return",
            reason_requested="Annual tax compliance and stability cross-check",
            source_policy_reference="Institutional Credit Policy Section 4.1",
            status_type="Conditional",
            applicable_stage="UNDERWRITING_REVIEW",
            accepted_formats=[".pdf"],
            verification_method="ITR acknowledgement verification"
        )
    ]

    @classmethod
    def get_document_checklist(cls) -> List[DocumentRequirementItem]:
        """Return the official Personal Loan document checklist."""
        return cls.DOCUMENT_REQUIREMENTS

    @classmethod
    def evaluate_rules(cls, applicant_data: Dict[str, Any], financial_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate Personal Loan specific policy rules."""
        evaluations = []
        dti = financial_data.get("dti_ratio", 0.0)
        monthly_income = float(applicant_data.get("monthly_income", 0.0))
        age = int(applicant_data.get("age", 25))
        emp_months = int(applicant_data.get("employment_months", 0))

        # DTI Rule
        evaluations.append({
            "rule_id": "PL-RULE-DTI",
            "name": "Personal Loan Debt-to-Income Ceiling",
            "condition": "dti_ratio <= 0.55",
            "severity": "BLOCKING",
            "result": "PASS" if dti <= 0.55 else "FAIL",
            "explanation": f"Calculated DTI {round(dti*100, 1)}% {'is within' if dti <= 0.55 else 'exceeds'} maximum 55% ceiling.",
            "human_review_required": dti > 0.55,
            "policy_category": "Authorized Lender Policy",
            "regulatory_reference": "RBI Fair Practices Code"
        })

        # Minimum Income
        evaluations.append({
            "rule_id": "PL-RULE-MIN-INCOME",
            "name": "Minimum Net Monthly Income",
            "condition": "monthly_income >= 15000",
            "severity": "BLOCKING",
            "result": "PASS" if monthly_income >= 15000.0 else "FAIL",
            "explanation": f"Monthly income INR {monthly_income:,.2f} {'satisfies' if monthly_income >= 15000.0 else 'is below'} baseline INR 15,000.",
            "human_review_required": monthly_income < 15000.0,
            "policy_category": "Authorized Lender Policy",
            "regulatory_reference": "Institutional Underwriting Manual"
        })

        # Employment Stability
        evaluations.append({
            "rule_id": "PL-RULE-EMP-STABILITY",
            "name": "Minimum Employment Duration",
            "condition": "employment_months >= 6",
            "severity": "WARNING",
            "result": "PASS" if emp_months >= 6 else "FAIL",
            "explanation": f"Tenure {emp_months} months {'satisfies' if emp_months >= 6 else 'is below'} desired 6 months continuous employment.",
            "human_review_required": emp_months < 6,
            "policy_category": "Authorized Lender Policy",
            "regulatory_reference": "Credit Policy Manual"
        })

        return evaluations
