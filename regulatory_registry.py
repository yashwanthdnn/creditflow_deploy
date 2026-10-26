"""
Regulatory Source Registry for CreditFlow AI:
Structured registry of regulatory circulars, lender policies, product rules,
and academic demonstration assumptions categorized strictly into four tiers.
"""

from typing import Dict, Any, List


class RegulatorySourceRegistry:
    """
    Authoritative reference registry mapping lending rules to published circulars,
    lender policies, product terms, and academic prototype boundaries.
    """

    REGULATORY_REQUIREMENTS = [
        {
            "id": "REG-RBI-DLG-2022-01",
            "source_name": "Reserve Bank of India (RBI)",
            "official_url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12382&Mode=0",
            "circular_reference": "RBI/2022-23/111 DOR.CRE.REC.66/21.07.001/2022-23 (Digital Lending Guidelines)",
            "publication_date": "2022-09-02",
            "effective_date": "2022-11-30",
            "applicable_lender_type": "All Commercial Banks & NBFCs",
            "applicable_product": "ALL",
            "plain_language_summary": "All digital loan sanctions must disclose All-inclusive Annual Percentage Rate (APR) and Key Fact Statement (KFS) prior to agreement execution.",
            "system_control": "FinancialEngine.calculate_apr & KFS summary generation in assessment dossier",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "REG-RBI-DLG-2022-02",
            "source_name": "Reserve Bank of India (RBI)",
            "official_url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12382&Mode=0",
            "circular_reference": "Section 4.1, Data Minimization & Consent Mandate",
            "publication_date": "2022-09-02",
            "effective_date": "2022-11-30",
            "applicable_lender_type": "Digital Lending Platforms & Regulated Entities",
            "applicable_product": "ALL",
            "plain_language_summary": "Lending systems must strictly practice data minimization: no biometric access, no storage of passwords/OTPs, and mandatory prior consent.",
            "system_control": "DataValidationAgent consent validation & secure exclusion of credentials from SQLite schema",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "REG-IBA-EDULOAN-2021",
            "source_name": "Indian Banks' Association (IBA) / RBI Guidance",
            "official_url": "https://www.iba.org.in/guidelines/model-educational-loan-scheme.html",
            "circular_reference": "IBA Model Educational Loan Scheme for Pursuing Higher Education in India and Abroad (Revision V)",
            "publication_date": "2021-05-15",
            "effective_date": "2021-06-01",
            "applicable_lender_type": "Scheduled Commercial Banks",
            "applicable_product": "EDUCATION_LOAN",
            "plain_language_summary": "Mandates study-period moratorium (Course Duration + 6 to 12 months grace period). Students without independent income are evaluated based on co-applicant support.",
            "system_control": "FinancialEngine.calculate_education_moratorium_and_repayment with separate co-applicant underwriting",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "REG-RBI-FPC-2015",
            "source_name": "Reserve Bank of India (RBI)",
            "official_url": "https://rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10585",
            "circular_reference": "Master Direction - Non-Banking Financial Company - Systemically Important Non-Deposit taking (Fair Practices Code)",
            "publication_date": "2015-07-01",
            "effective_date": "2015-07-01",
            "applicable_lender_type": "NBFCs & Banks",
            "applicable_product": "ALL",
            "plain_language_summary": "Right to reason: Lenders must clearly convey rejection or adverse underwriting reasons in writing to the applicant.",
            "system_control": "RiskExplanationAgent evidence trail and underwriter human review summary",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        }
    ]

    LENDER_POLICIES = [
        {
            "id": "POL-LEND-DTI-CEILING",
            "policy_name": "Maximum Permissible Debt-to-Income / FOIR Ceiling",
            "policy_version": "v2.4",
            "applicable_product": "PERSONAL_LOAN",
            "plain_language_summary": "Total scheduled monthly debt obligations (existing + proposed EMI) must not exceed 55% of verifiable monthly take-home income.",
            "system_control": "FinancialEngine DTI calculation & EligibilityRulesAgent RULE_MAX_DTI",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "POL-LEND-MIN-AGE",
            "policy_name": "Minimum Legal Age at Loan Origination",
            "policy_version": "v2.4",
            "applicable_product": "ALL",
            "plain_language_summary": "Applicant must be at least 18 years of age. For student applicants under 18, a legal guardian co-applicant is mandatory.",
            "system_control": "DataValidationAgent & EligibilityRulesAgent RULE_AGE_MIN",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "POL-LEND-EDU-COAPP",
            "policy_name": "Mandatory Co-Applicant for Higher Education Loans",
            "policy_version": "v2.4",
            "applicable_product": "EDUCATION_LOAN",
            "plain_language_summary": "For education loans exceeding INR 4,00,000, a parent or legal guardian co-applicant with verifiable income is required as joint borrower.",
            "system_control": "EducationLoanPolicy.evaluate_co_applicant_requirement",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        }
    ]

    PRODUCT_TERMS = [
        {
            "id": "TERM-PL-FIXED-AMORT",
            "product_name": "Unsecured Personal Loan Terms",
            "term_version": "v2.4",
            "applicable_product": "PERSONAL_LOAN",
            "plain_language_summary": "Nominal rate: 10.5% - 18.0% p.a. Reducing-balance amortization. Standard tenure: 12 to 60 months. Upfront processing fee: 1.0% + GST.",
            "system_control": "FinancialEngine.calculate_net_disbursement & calculate_apr",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        },
        {
            "id": "TERM-EDU-MORATORIUM-TERMS",
            "product_name": "Higher Education Loan Terms",
            "term_version": "v2.4",
            "applicable_product": "EDUCATION_LOAN",
            "plain_language_summary": "Nominal rate: 9.5% - 12.5% p.a. Simple interest during moratorium. Repayment begins 6 months after course completion. Tenure up to 120 months.",
            "system_control": "FinancialEngine.calculate_education_moratorium_and_repayment",
            "control_status": "IMPLEMENTED_AND_TESTED",
            "last_reviewed_date": "2026-10-26"
        }
    ]

    ACADEMIC_ASSUMPTIONS = [
        {
            "id": "ASSUME-SYNTHETIC-SANDBOX",
            "category": "Academic Demonstration Scope",
            "description": "All customer records, bank statements, institution documents, and Aadhaar/PAN tokens operate strictly in simulation mode.",
            "rationale": "Protects real applicant privacy; ensures zero dependency on proprietary paid API gateways."
        },
        {
            "id": "ASSUME-DISBURSEMENT-LOCK",
            "category": "Safety Control",
            "description": "Real fund transfers, bank clearing, and automated disbursements are hard-coded disabled in this educational prototype.",
            "rationale": "Prevents accidental or unauthorized capital movement during classroom testing."
        }
    ]

    @classmethod
    def get_rules_for_product(cls, loan_product: str) -> Dict[str, List[Dict[str, Any]]]:
        """Filter regulatory and policy controls by selected loan product."""
        reg_filtered = [
            r for r in cls.REGULATORY_REQUIREMENTS
            if r["applicable_product"] in [loan_product, "ALL"]
        ]
        pol_filtered = [
            p for p in cls.LENDER_POLICIES
            if p["applicable_product"] in [loan_product, "ALL"]
        ]
        terms_filtered = [
            t for t in cls.PRODUCT_TERMS
            if loan_product == "ALL" or t["applicable_product"] == loan_product
        ]

        return {
            "regulatory_requirements": reg_filtered,
            "lender_policies": pol_filtered,
            "product_terms": terms_filtered,
            "academic_assumptions": cls.ACADEMIC_ASSUMPTIONS
        }

    @classmethod
    def get_all_sources(cls, product_filter: str = "ALL") -> Dict[str, List[Dict[str, Any]]]:
        """Return all sources optionally filtered by product."""
        return cls.get_rules_for_product(product_filter)
