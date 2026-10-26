"""
Agent 2: Data Validation Agent.
Validates applicant fields, ranges, logical integrity, document completeness,
detects duplicate records, checks institutional consistency for Education Loans,
and field-to-document mismatches.
"""

from typing import Dict, Any, List, Optional
from models.schemas import DataValidationResult
from services.database import get_db_connection
from services.personal_loan_policy import PersonalLoanPolicy
from services.education_loan_policy import EducationLoanPolicy


class DataValidationAgent:
    """Agent 2: Responsible for verifying data integrity, field constraints, and document completeness."""

    def __init__(self):
        pass

    def validate(
        self,
        applicant_data: Dict[str, Any],
        uploaded_documents: Optional[List[Dict[str, Any]]] = None
    ) -> DataValidationResult:
        blocking_errors: List[str] = []
        warnings: List[str] = []
        missing_fields: List[str] = []
        duplicate_flags: List[str] = []
        inconsistency_flags: List[str] = []
        document_status_map: Dict[str, str] = {}

        loan_product = applicant_data.get("loan_product", "PERSONAL_LOAN")

        # 1. Base Required Field Checks
        base_required_fields = [
            ("full_name", "Applicant Full Name"),
            ("email", "Contact Email"),
            ("phone", "Contact Phone"),
            ("date_of_birth", "Date of Birth"),
            ("requested_loan_amount", "Requested Loan Amount"),
            ("loan_tenure_months", "Loan Tenure")
        ]

        for field_key, field_label in base_required_fields:
            val = applicant_data.get(field_key)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing_fields.append(field_label)
                blocking_errors.append(f"Missing mandatory field: {field_label}")

        # 2. Product-Specific Fields & Income Checks
        monthly_income = float(applicant_data.get("monthly_income") or 0.0)
        co_applicant_income = float(applicant_data.get("co_applicant_income") or 0.0)

        if loan_product == "EDUCATION_LOAN":
            # For Education Loan, student income is separate from co-applicant income.
            # Missing student salary must NOT result in rejection.
            edu_fields = [
                ("university_name", "University Name"),
                ("college_institution_name", "College or Institution Name"),
                ("course_name", "Course Name"),
                ("college_pin_code", "College PIN Code"),
                ("admission_status", "Admission Status")
            ]
            for f_key, f_label in edu_fields:
                val = applicant_data.get(f_key)
                if val is None or (isinstance(val, str) and not val.strip()):
                    missing_fields.append(f_label)
                    blocking_errors.append(f"Missing mandatory education field: {f_label}")

            # Validate institution consistency (Section A.4)
            is_consistent, inst_status, inst_warnings = EducationLoanPolicy.validate_institution_consistency(applicant_data)
            if not is_consistent:
                inconsistency_flags.extend(inst_warnings)
            elif inst_warnings:
                warnings.extend(inst_warnings)

            # Check co-applicant requirement for loan amount > 400,000
            req_amount = float(applicant_data.get("requested_loan_amount") or 0.0)
            if req_amount > 400000.0:
                co_name = applicant_data.get("co_applicant_name")
                if not co_name or not str(co_name).strip() or co_applicant_income <= 0:
                    blocking_errors.append("Education loans exceeding INR 4 Lakhs mandate a financial co-applicant with verified income.")
                    missing_fields.append("Co-Applicant Name & Income Proof")

        else:
            # PERSONAL LOAN: Salaried/Self-Employed income is required
            if monthly_income <= 0:
                blocking_errors.append("Declared monthly take-home income must be greater than zero for Personal Loan.")
                missing_fields.append("Monthly Income")
            elif monthly_income < 10000:
                warnings.append(f"Declared monthly income ({monthly_income}) is unusually low for loan servicing.")

            emp_type = applicant_data.get("employment_type")
            if not emp_type or not str(emp_type).strip():
                warnings.append("Employment type not explicitly declared; defaulting to Salaried.")

        # 3. Permitted Range & Logical Consistency
        age = int(applicant_data.get("age") or 0)
        if age < 18:
            blocking_errors.append(f"Applicant age ({age}) is below legal age of 18.")
        elif age > 90:
            blocking_errors.append(f"Applicant age ({age}) exceeds maximum permissible limit.")

        loan_amount = float(applicant_data.get("requested_loan_amount") or 0.0)
        if loan_amount <= 0:
            blocking_errors.append("Requested loan amount must be positive.")

        tenure = int(applicant_data.get("loan_tenure_months") or 0)
        if tenure <= 0 or tenure > 360:
            blocking_errors.append(f"Loan tenure ({tenure} months) is out of permitted range (1 to 360).")

        existing_emi = float(applicant_data.get("existing_monthly_obligations") or 0.0)
        if existing_emi < 0:
            blocking_errors.append("Existing monthly debt obligations cannot be negative.")

        effective_income = (monthly_income + co_applicant_income) if loan_product == "EDUCATION_LOAN" else monthly_income
        if effective_income > 0 and existing_emi >= effective_income:
            inconsistency_flags.append(
                f"Existing obligations ({existing_emi}) equal or exceed effective income ({effective_income})."
            )

        # 4. Duplicate Application / National ID Check
        national_id = applicant_data.get("national_id_number")
        current_app_id = applicant_data.get("application_id", "")
        if national_id and national_id != "MASKED-XXXX":
            try:
                conn = get_db_connection()
                dup_row = conn.execute("""
                    SELECT a.application_id, ap.full_name
                    FROM applications a
                    JOIN applicants ap ON a.applicant_id = ap.applicant_id
                    WHERE ap.national_id_masked = ? AND a.application_id != ?
                    LIMIT 1
                """, (national_id, current_app_id)).fetchone()
                conn.close()

                if dup_row:
                    duplicate_flags.append(
                        f"Duplicate identity detected: National ID matches existing application {dup_row['application_id']} ({dup_row['full_name']})."
                    )
            except Exception:
                pass

        # 5. Document Completeness Check
        CATEGORY_ALIASES = {
            "IDENTITY_PROOF": ["REQ-PL-ID", "REQ-EDU-STUDENT-KYC"],
            "ADDRESS_PROOF": ["REQ-PL-ADDR", "REQ-EDU-STUDENT-KYC"],
            "PHOTOGRAPH": ["REQ-PL-PHOTO"],
            "INCOME_PROOF": ["REQ-PL-SALARY-SLIPS", "REQ-PL-BANK-STMT", "REQ-EDU-COAPP-INCOME"],
            "SALARY_SLIP": ["REQ-PL-SALARY-SLIPS"],
            "BANK_STATEMENT": ["REQ-PL-BANK-STMT"],
            "FORM16": ["REQ-PL-FORM16"],
            "OFFER_LETTER": ["REQ-EDU-OFFER-LETTER"],
            "FEE_STRUCTURE": ["REQ-EDU-FEE-STRUCTURE"],
            "ACADEMIC_RECORDS": ["REQ-EDU-ACADEMIC-RECORDS"]
        }

        if loan_product == "EDUCATION_LOAN":
            req_items = EducationLoanPolicy.get_document_checklist()
        else:
            req_items = PersonalLoanPolicy.get_document_checklist()

        uploaded_req_ids = set()
        if uploaded_documents:
            for doc in uploaded_documents:
                req_id = doc.get("requirement_id") or doc.get("doc_category")
                if req_id:
                    uploaded_req_ids.add(req_id)
                    document_status_map[req_id] = doc.get("status", "Uploaded")
                    for alias in CATEGORY_ALIASES.get(req_id, []):
                        uploaded_req_ids.add(alias)
                        document_status_map[alias] = doc.get("status", "Uploaded")

        for req in req_items:
            if req.status_type == "Mandatory" and req.requirement_id not in uploaded_req_ids:
                missing_fields.append(f"Mandatory Document: {req.document_name}")
                warnings.append(f"Missing mandatory document: {req.document_name} ({req.requirement_id})")
                document_status_map[req.requirement_id] = "Not Uploaded"

        # 6. Mismatch between Extracted Document Fields and Form Data
        if uploaded_documents:
            for doc in uploaded_documents:
                extracted = doc.get("extracted_fields") or {}
                # Check income mismatch for Personal Loan
                if loan_product == "PERSONAL_LOAN":
                    det_income = extracted.get("detected_monthly_income")
                    if det_income and monthly_income > 0:
                        diff_pct = abs(monthly_income - det_income) / monthly_income
                        if diff_pct > 0.35:
                            inconsistency_flags.append(
                                f"Income mismatch: Form declared {monthly_income}, but document indicates {det_income} (diff {round(diff_pct*100)}%)."
                            )
                # Check name mismatch
                det_name = extracted.get("detected_name")
                form_name = applicant_data.get("full_name", "").strip().lower()
                if det_name and form_name:
                    det_name_clean = det_name.strip().lower()
                    if form_name not in det_name_clean and det_name_clean not in form_name:
                        warnings.append(
                            f"Name variation: Form name '{applicant_data.get('full_name')}' differs from document text '{det_name}'."
                        )

        # 7. Action Determination
        is_valid = len(blocking_errors) == 0

        if inconsistency_flags or duplicate_flags:
            action = "HUMAN_REVIEW_REQUIRED"
        elif missing_fields or blocking_errors:
            action = "MORE_INFORMATION_REQUIRED"
        elif warnings:
            action = "PROCEED_WITH_WARNINGS"
        else:
            action = "PROCEED"

        return DataValidationResult(
            is_valid=is_valid,
            blocking_errors=blocking_errors,
            warnings=warnings,
            missing_fields=missing_fields,
            document_status=document_status_map,
            duplicate_flags=duplicate_flags,
            inconsistency_flags=inconsistency_flags,
            recommended_action=action
        )
