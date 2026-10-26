"""
Pydantic schemas and structured validation models for CreditFlow AI:
Personal Loan and Education Loan products, 12 document statuses,
expense reconciliations, and financial methodology definitions.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ApplicationStatus(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    VALIDATED = "VALIDATED"
    FINANCIAL_ANALYSIS_COMPLETED = "FINANCIAL_ANALYSIS_COMPLETED"
    RULE_CHECK_COMPLETED = "RULE_CHECK_COMPLETED"
    RISK_ASSESSED = "RISK_ASSESSED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    PRE_SCREENING_COMPLETED = "PRE_SCREENING_COMPLETED"
    FINAL_DECISION_PENDING = "FINAL_DECISION_PENDING"
    APPROVED_BY_AUTHORIZED_LENDER = "APPROVED_BY_AUTHORIZED_LENDER"
    DECLINED_BY_AUTHORIZED_LENDER = "DECLINED_BY_AUTHORIZED_LENDER"
    DISBURSEMENT_PENDING = "DISBURSEMENT_PENDING"
    DISBURSED = "DISBURSED"
    ON_HOLD = "ON_HOLD"
    COMPLAINT_OPEN = "COMPLAINT_OPEN"
    DISPUTED = "DISPUTED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


class PreliminaryOutcome(str, Enum):
    PROCEED_TO_NEXT_STAGE = "PROCEED_TO_NEXT_STAGE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    ON_HOLD_FOR_VERIFICATION = "ON_HOLD_FOR_VERIFICATION"


# Exactly the 12 Document Status States required in Section C
class DocumentStatus(str, Enum):
    NOT_UPLOADED = "Not Uploaded"
    UPLOADED = "Uploaded"
    FILE_VALIDATION_FAILED = "File Validation Failed"
    EXTRACTION_PENDING = "Extraction Pending"
    EXTRACTION_COMPLETED = "Extraction Completed"
    AWAITING_APPLICANT_CONFIRMATION = "Awaiting Applicant Confirmation"
    MISSING_INFORMATION = "Missing Information"
    MISMATCH_DETECTED = "Mismatch Detected"
    REUPLOAD_REQUIRED = "Re-upload Required"
    AWAITING_AUTHORIZED_VERIFICATION = "Awaiting Authorized Verification"
    VERIFIED_THROUGH_AUTHORIZED_INTEGRATION = "Verified Through Authorized Integration"
    HUMAN_REVIEW_REQUIRED = "Human Review Required"


class EmploymentType(str, Enum):
    SALARIED_FULL_TIME = "Salaried Full-Time"
    SALARIED_PART_TIME = "Salaried Part-Time"
    SELF_EMPLOYED_PROFESSIONAL = "Self-Employed Professional"
    SELF_EMPLOYED_BUSINESS = "Self-Employed Business"
    STUDENT = "Student"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"


class LoanProductType(str, Enum):
    PERSONAL_LOAN = "PERSONAL_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"


class AdmissionStatus(str, Enum):
    APPLIED = "Applied"
    PROVISIONAL_OFFER_RECEIVED = "Provisional Offer Received"
    CONFIRMED_ADMISSION = "Confirmed Admission"


class InterestRateType(str, Enum):
    FIXED = "Fixed"
    FLOATING = "Floating"


class ExpenseReconciliation(BaseModel):
    """Education Cost Reconciliation Schema (Section A.2)."""
    total_declared_eligible_expenses: float
    confirmed_scholarships: float = 0.0
    unconfirmed_scholarships: float = 0.0
    other_funding_sources: float = 0.0
    student_contribution: float = 0.0
    indicative_financing_requirement: float
    is_provisional: bool = True
    disclaimer: str = (
        "Provisional estimation based on declared institutional fees and submitted evidence. "
        "Unconfirmed scholarships are excluded from automatic deduction until official award confirmation."
    )


class AmortizationScheduleRow(BaseModel):
    month: int
    opening_balance: float
    monthly_payment: float
    principal_component: float
    interest_component: float
    closing_balance: float


class ApplicantData(BaseModel):
    """
    Unified applicant data supporting both Personal Loan and Education Loan products.
    """
    application_id: Optional[str] = None
    applicant_id: Optional[str] = None
    loan_product: str = Field(default=LoanProductType.PERSONAL_LOAN.value)
    policy_version: str = Field(default="v2.4")

    # Common applicant details
    full_name: str = Field(..., min_length=2, description="Applicant/Student legal name")
    email: str = Field(..., description="Contact email address")
    phone: str = Field(..., min_length=7, description="Contact phone number")
    date_of_birth: str = Field(..., description="Date of birth YYYY-MM-DD")
    age: int = Field(..., ge=15, le=100, description="Age in completed years")
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    nationality: str = Field(default="Indian")
    consent_given: bool = Field(..., description="Consent for data processing and credit inquiries")
    national_id_number: Optional[str] = Field(default=None, description="Masked/Synthetic Identity document number")

    # --- PERSONAL LOAN SPECIFIC FIELDS ---
    employment_type: str = Field(default=EmploymentType.SALARIED_FULL_TIME.value)
    employer_name: Optional[str] = None
    occupation: Optional[str] = None
    employment_months: int = Field(default=12, ge=0)
    monthly_income: float = Field(default=0.0, ge=0)  # Take-home
    monthly_gross_income: float = Field(default=0.0, ge=0)
    other_income: float = Field(default=0.0, ge=0)
    existing_monthly_obligations: float = Field(default=0.0, ge=0)
    dependents: int = Field(default=0, ge=0, le=20)
    loan_purpose: Optional[str] = None
    interest_rate_type: str = Field(default=InterestRateType.FIXED.value)
    credit_bureau_source: Optional[str] = Field(default="Synthetic Bureau Sandbox")
    credit_bureau_date: Optional[str] = None
    credit_score: Optional[int] = Field(default=None, ge=300, le=900)
    previous_defaults_count: int = Field(default=0, ge=0)

    # Loan terms
    requested_loan_amount: float = Field(..., gt=0)
    loan_tenure_months: int = Field(..., ge=1, le=360)
    proposed_interest_rate: float = Field(default=12.0, ge=0.0, le=40.0)

    # --- EDUCATION LOAN SPECIFIC FIELDS ---
    university_name: Optional[str] = None
    college_name: Optional[str] = None
    institution_address: Optional[str] = None
    college_pin_code: Optional[str] = None
    city_district_state: Optional[str] = None
    country_of_study: str = Field(default="India")
    institution_type: Optional[str] = Field(default="Recognized University")
    course_name: Optional[str] = None
    course_qualification: Optional[str] = None
    course_duration_months: int = Field(default=24, ge=1, le=84)
    course_start_date: Optional[str] = None
    course_completion_date: Optional[str] = None
    admission_status: str = Field(default=AdmissionStatus.PROVISIONAL_OFFER_RECEIVED.value)
    admission_letter_number: Optional[str] = None
    entrance_exam_details: Optional[str] = None

    # Education Costs Breakdown
    tuition_fees: float = Field(default=0.0, ge=0)
    admission_registration_fees: float = Field(default=0.0, ge=0)
    examination_fees: float = Field(default=0.0, ge=0)
    hostel_accommodation_fees: float = Field(default=0.0, ge=0)
    books_equipment_fees: float = Field(default=0.0, ge=0)
    travel_living_expenses: float = Field(default=0.0, ge=0)
    total_course_cost: float = Field(default=0.0, ge=0)

    # Funding sources
    confirmed_scholarship_amount: float = Field(default=0.0, ge=0)
    unconfirmed_scholarship_amount: float = Field(default=0.0, ge=0)
    other_funding_sources: float = Field(default=0.0, ge=0)
    student_contribution: float = Field(default=0.0, ge=0)

    # Parent / Co-applicant Details
    co_applicant_name: Optional[str] = None
    co_applicant_relation: Optional[str] = None
    co_applicant_income: float = Field(default=0.0, ge=0)
    co_applicant_existing_emi: float = Field(default=0.0, ge=0)
    co_applicant_credit_score: Optional[int] = Field(default=None, ge=300, le=900)

    # Subsidy & Moratorium
    moratorium_months: int = Field(default=30, ge=0, le=96)  # Course + 6 months
    interest_subsidy_scheme: Optional[str] = None  # e.g. "CSIS"
    interest_subsidy_status: str = Field(default="Eligibility pending verification")


class DocumentRequirementItem(BaseModel):
    """Specification of a document requirement in product checklists."""
    requirement_id: str
    document_name: str
    reason_requested: str
    source_policy_reference: str
    status_type: str  # Mandatory, Conditional, Optional
    applicable_stage: str
    accepted_formats: List[str]
    verification_method: str
    review_status: str = DocumentStatus.NOT_UPLOADED.value


class DocumentMetadata(BaseModel):
    doc_id: str
    application_id: str
    doc_category: str
    original_filename: str
    file_path: str
    file_size_bytes: int
    content_type: str
    status: str = DocumentStatus.UPLOADED.value
    extracted_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    confirmed_by_applicant: bool = False
    verification_notes: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


# --- Structured Agent Output Schemas ---

class DataValidationResult(BaseModel):
    is_valid: bool
    blocking_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    document_status: Dict[str, str] = Field(default_factory=dict)
    duplicate_flags: List[str] = Field(default_factory=list)
    inconsistency_flags: List[str] = Field(default_factory=list)
    institution_consistency_status: Optional[str] = None
    recommended_action: str


class FinancialAnalysisResult(BaseModel):
    loan_product: str = Field(default=LoanProductType.PERSONAL_LOAN.value)
    monthly_emi: float = 0.0
    total_scheduled_repayment: float = 0.0
    total_scheduled_interest: float = 0.0
    existing_obligations: float = 0.0
    total_monthly_obligations: float = 0.0
    dti_ratio: float = 0.0
    loan_to_annual_income: float = 0.0
    net_disposable_income: float = 0.0
    upfront_charges: float = 0.0
    net_disbursement: float = 0.0
    annual_percentage_rate: Optional[float] = None  # APR %
    # Education Loan specific
    moratorium_months: int = 0
    study_period_interest: float = 0.0
    capitalized_loan_at_repayment: float = 0.0
    expense_reconciliation: Optional[ExpenseReconciliation] = None
    risk_indicators: Dict[str, Any] = Field(default_factory=dict)
    repayment_indicators: Dict[str, str] = Field(default_factory=dict)
    calculation_assumptions: Dict[str, Any] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    is_reliable: bool = True
    calculation_explanation: str = ""
    engine_version: str = "FinEngine-v2.4"


class RuleEvaluationItem(BaseModel):
    rule_id: str
    name: str
    condition: str
    severity: str  # BLOCKING, WARNING, INFO
    result: str    # PASS, FAIL, SKIPPED
    explanation: str
    human_review_required: bool
    policy_category: str = "Authorized Lender Policy"
    regulatory_reference: Optional[str] = None


class EligibilityRulesResult(BaseModel):
    loan_product: str = Field(default=LoanProductType.PERSONAL_LOAN.value)
    policy_version: str = Field(default="v2.4")
    rules_evaluated: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    rule_items: List[RuleEvaluationItem] = Field(default_factory=list)
    requires_human_review: bool = False
    summary: str = ""
    preliminary_eligibility: str = "ELIGIBLE_PRE_SCREEN"


class CreditRiskResult(BaseModel):
    risk_score: Optional[float] = None
    risk_category: str
    model_version: str
    model_name: str
    features_used: List[str] = Field(default_factory=list)
    inference_timestamp: str
    is_prediction_reliable: bool
    limitations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    explanation_notes: str


class RiskExplanationResult(BaseModel):
    loan_product: str = Field(default=LoanProductType.PERSONAL_LOAN.value)
    preliminary_outcome: PreliminaryOutcome
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)
    evidence_trail: List[str] = Field(default_factory=list)
    human_review_summary: Optional[str] = None
    pause_reason: Optional[str] = None
    escalation_flags: List[str] = Field(default_factory=list)
    disclaimer: str


class RecordManagementResult(BaseModel):
    record_saved: bool
    application_id: str
    audit_log_count: int
    database_status: str
    message: str


class AgentRunLog(BaseModel):
    agent_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str
    input_summary: str
    output_summary: str
    escalation_reason: Optional[str] = None
