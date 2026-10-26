"""
Education Loan Policy, Institutional Verification, and Document Checklist Service:
Encapsulates admissions verification, institution consistency checks, separate co-applicant affordability,
expense reconciliation, and moratorium underwriting strictly dedicated to Education Loans.
"""

import re
from typing import Dict, Any, List, Tuple
from models.schemas import DocumentRequirementItem, DocumentStatus


class EducationLoanPolicy:
    """Dedicated policy engine and document checklist for Higher Education Loans."""

    POLICY_VERSION = "v2.4-education"

    DOCUMENT_REQUIREMENTS: List[DocumentRequirementItem] = [
        DocumentRequirementItem(
            requirement_id="REQ-EDU-OFFER-LETTER",
            document_name="Admission or Provisional Offer Letter",
            reason_requested="Proof of secured admission, course name, and institution enrollment",
            source_policy_reference="IBA Model Educational Loan Scheme Section 4.2",
            status_type="Mandatory",
            applicable_stage="ADMISSION_VERIFICATION",
            accepted_formats=[".pdf"],
            verification_method="Official institution letterhead verification, admission number verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-FEE-STRUCTURE",
            document_name="Institutional Fee Structure Breakdown",
            reason_requested="Itemized official estimate of tuition, examination, hostel, and laboratory fees",
            source_policy_reference="IBA Model Educational Loan Scheme Section 5.1",
            status_type="Mandatory",
            applicable_stage="COST_RECONCILIATION",
            accepted_formats=[".pdf"],
            verification_method="Reconcile against declared semester expenses"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-ACADEMIC-RECORDS",
            document_name="Academic Marksheets & Degree Certificates (10th/12th/Graduation)",
            reason_requested="Evaluation of student academic consistency and course eligibility",
            source_policy_reference="Institutional Education Underwriting Norms Section 2.1",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="Marksheet serial numbers and academic institution verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-ENTRANCE-SCORECARD",
            document_name="Entrance Exam Scorecard (e.g. JEE/CAT/GATE/GRE/GMAT/IELTS)",
            reason_requested="Evidence of merit ranking or language proficiency for overseas courses",
            source_policy_reference="Institutional Credit Policy Section 4.3",
            status_type="Conditional",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".png"],
            verification_method="Scorecard reference number check against testing body format"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-STUDENT-KYC",
            document_name="Student Government Identity & Address Proof",
            reason_requested="Legal KYC identification for primary student applicant",
            source_policy_reference="RBI Master Direction - KYC Direction, 2016",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="Masked ID verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-COAPP-KYC",
            document_name="Parent / Co-Applicant Identity & Address Proof",
            reason_requested="Mandatory joint-borrower KYC verification",
            source_policy_reference="IBA Model Educational Loan Scheme Section 6.1",
            status_type="Mandatory",
            applicable_stage="INTAKE",
            accepted_formats=[".pdf", ".jpg", ".jpeg", ".png"],
            verification_method="Co-applicant identity verification token"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-COAPP-INCOME",
            document_name="Parent / Co-Applicant Income Proof & Bank Statements (6 Months)",
            reason_requested="Verifies co-applicant debt servicing capability during and after study period",
            source_policy_reference="Institutional Credit Policy Section 6.2",
            status_type="Mandatory",
            applicable_stage="FINANCIAL_ANALYSIS",
            accepted_formats=[".pdf"],
            verification_method="Salary slip / ITR / Bank account inflow verification"
        ),
        DocumentRequirementItem(
            requirement_id="REQ-EDU-SCHOLARSHIP-LETTER",
            document_name="Official Scholarship / Grant Award Letter",
            reason_requested="Confirms external non-repayable grant deductions from tuition costs",
            source_policy_reference="Institutional Policy Section 5.3",
            status_type="Conditional",
            applicable_stage="COST_RECONCILIATION",
            accepted_formats=[".pdf"],
            verification_method="Award issuing authority verification"
        )
    ]

    @classmethod
    def get_document_checklist(cls) -> List[DocumentRequirementItem]:
        """Return the official Education Loan document checklist."""
        return cls.DOCUMENT_REQUIREMENTS

    @classmethod
    def validate_institution_consistency(cls, applicant_data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """
        Validate that institution name, address, PIN code, city, state, country,
        course, and admission status are internally consistent (Section A.4).
        """
        warnings = []
        is_consistent = True

        pin = str(applicant_data.get("college_pin_code") or "").strip()
        state = str(applicant_data.get("city_district_state") or "").strip()
        country = str(applicant_data.get("country_of_study") or "India").strip()
        admission_status = str(applicant_data.get("admission_status") or "").strip()
        letter_no = str(applicant_data.get("admission_letter_number") or "").strip()

        # PIN code format for India
        if country.lower() == "india":
            if pin and not re.match(r"^[1-9][0-9]{5}$", pin):
                warnings.append(f"Institutional PIN code '{pin}' is not a valid 6-digit postal code.")
                is_consistent = False

            # Check PIN code initial digit matches Northern/Southern/Western zone
            if pin and len(pin) == 6:
                pin_prefix = pin[0]
                if pin_prefix in ["1", "2"] and "south" in state.lower():
                    warnings.append(f"Postal zone conflict: PIN prefix '{pin_prefix}' typically indicates Northern region, but state says '{state}'.")
                elif pin_prefix in ["5", "6"] and ("delhi" in state.lower() or "punjab" in state.lower()):
                    warnings.append(f"Postal zone conflict: PIN prefix '{pin_prefix}' indicates Southern region, but state says '{state}'.")

        # Admission status vs letter number check
        if admission_status == "Confirmed Admission" and not letter_no:
            warnings.append("Confirmed Admission declared, but official admission or enrollment number is missing.")
            is_consistent = False

        status_msg = "Institution details submitted — independent verification pending."
        if is_consistent and not warnings:
            status_msg = "Institution details submitted — internally consistent. (Independent accreditation verification pending)."

        return is_consistent, status_msg, warnings

    @classmethod
    def evaluate_rules(
        cls,
        applicant_data: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate Education Loan specific policy rules.
        IMPORTANT: Evaluates co-applicant income; missing student salary is NEVER penalized!
        """
        evaluations = []
        loan_amount = float(applicant_data.get("requested_loan_amount", 0.0))
        co_income = float(applicant_data.get("co_applicant_income", 0.0))
        co_emi = float(applicant_data.get("co_applicant_existing_emi", 0.0))
        admission_status = applicant_data.get("admission_status", "Applied")

        # 1. Co-Applicant Mandate for > 4 Lakhs
        if loan_amount > 400000.0:
            coapp_passed = bool(applicant_data.get("co_applicant_name")) and co_income > 0
            evaluations.append({
                "rule_id": "EDU-RULE-COAPP-MANDATORY",
                "name": "Mandatory Parent / Co-Applicant Guarantee (> INR 4 Lakhs)",
                "condition": "loan_amount > 400000 implies co_applicant_income > 0",
                "severity": "BLOCKING",
                "result": "PASS" if coapp_passed else "FAIL",
                "explanation": (
                    f"Co-applicant '{applicant_data.get('co_applicant_name') or 'None'}' with monthly income "
                    f"INR {co_income:,.2f} {'provided' if coapp_passed else 'required for education loans over INR 4 Lakhs'}."
                ),
                "human_review_required": not coapp_passed,
                "policy_category": "Authorized Lender Policy",
                "regulatory_reference": "IBA Model Educational Loan Scheme Section 6"
            })

        # 2. Co-Applicant Affordability / FOIR
        if co_income > 0:
            post_emi = financial_data.get("monthly_emi", 0.0)
            co_dti = round((co_emi + post_emi) / co_income, 4)
            dti_passed = co_dti <= 0.65  # Education loan permits up to 65% FOIR on parent income
            evaluations.append({
                "rule_id": "EDU-RULE-COAPP-AFFORDABILITY",
                "name": "Co-Applicant Repayment Obligation-to-Income (FOIR)",
                "condition": "co_dti <= 0.65",
                "severity": "WARNING",
                "result": "PASS" if dti_passed else "FAIL",
                "explanation": (
                    f"Parent/co-applicant projected obligation ratio is {round(co_dti*100, 1)}% "
                    f"({'within' if dti_passed else 'exceeds'} allowable 65% ceiling)."
                ),
                "human_review_required": not dti_passed,
                "policy_category": "Authorized Lender Policy",
                "regulatory_reference": "Credit Policy Manual"
            })
        else:
            evaluations.append({
                "rule_id": "EDU-RULE-STUDENT-INCOME-NOTE",
                "name": "Student Pre-Employment Independent Evaluation",
                "condition": "student_income == 0 is permissible",
                "severity": "INFO",
                "result": "PASS",
                "explanation": "Student has zero pre-course income. Assessed without penalty under student pre-employment policy.",
                "human_review_required": False,
                "policy_category": "Selected Loan Product Terms",
                "regulatory_reference": "IBA Educational Guidelines"
            })

        # 3. Admission Offer Verification
        admission_passed = admission_status in ["Provisional Offer Received", "Confirmed Admission"]
        evaluations.append({
            "rule_id": "EDU-RULE-ADMISSION-STATUS",
            "name": "Institutional Admission Offer Status",
            "condition": "admission_status in ['Provisional Offer Received', 'Confirmed Admission']",
            "severity": "BLOCKING" if admission_status == "Applied" else "INFO",
            "result": "PASS" if admission_passed else "FAIL",
            "explanation": (
                f"Admission status is '{admission_status}'. "
                f"{'Satisfies minimum provisional or confirmed baseline.' if admission_passed else 'Pure application stage requires confirmed offer letter before sanction.'}"
            ),
            "human_review_required": not admission_passed,
            "policy_category": "Authorized Lender Policy",
            "regulatory_reference": "IBA Section 4.2"
        })

        return evaluations
