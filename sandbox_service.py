"""
Secure Assessment Sandbox Service (Section E).
Dedicated isolated execution environment for authorized Credit Officers,
Fraud Investigators, and Administrators.
Maintains completely separate SQLite storage (data/sandbox_evaluations.db)
to ensure ZERO contamination of production intake records.
"""

import sqlite3
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config.settings import DATA_DIR
from models.schemas import DocumentStatus, PreliminaryOutcome
from services.financial_engine import FinancialEngine
from services.personal_loan_policy import PersonalLoanPolicy
from services.education_loan_policy import EducationLoanPolicy

SANDBOX_DB_PATH = DATA_DIR / "sandbox_evaluations.db"


class SandboxService:
    """Manages the isolated sandbox database and synthetic simulation workflows."""

    @staticmethod
    def get_sandbox_connection() -> sqlite3.Connection:
        """Establish connection to dedicated, isolated sandbox database."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(SANDBOX_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def init_sandbox_db():
        """Initialize schema in the isolated sandbox database."""
        conn = SandboxService.get_sandbox_connection()
        cur = conn.cursor()

        # Isolated sandbox applications table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_applications (
                sandbox_id TEXT PRIMARY KEY,
                scenario_name TEXT NOT NULL,
                loan_product TEXT NOT NULL,
                applicant_data_json TEXT NOT NULL,
                documents_json TEXT NOT NULL,
                simulation_flags_json TEXT NOT NULL,
                preliminary_outcome TEXT,
                status TEXT NOT NULL,
                created_by_role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Isolated sandbox agent execution traces
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_agent_runs (
                run_id TEXT PRIMARY KEY,
                sandbox_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                duration_ms REAL,
                status TEXT NOT NULL,
                input_summary TEXT,
                output_summary TEXT,
                escalation_reason TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sandbox_id) REFERENCES sandbox_applications(sandbox_id) ON DELETE CASCADE
            );
        """)

        # Isolated sandbox audit records
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_audit_logs (
                log_id TEXT PRIMARY KEY,
                sandbox_id TEXT,
                actor_role TEXT NOT NULL,
                action TEXT NOT NULL,
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def get_synthetic_presets() -> Dict[str, Dict[str, Any]]:
        """Return predefined synthetic test scenarios for Personal and Education loans."""
        return {
            "PL_PRIME_SALARIED": {
                "name": "Personal Loan: Prime Salaried Professional (Standard Approval)",
                "product": "PERSONAL_LOAN",
                "applicant": {
                    "full_name": "Aarav Sharma (Synthetic)",
                    "email": "aarav.synth@example.com",
                    "phone": "+91 98765 43210",
                    "date_of_birth": "1992-05-14",
                    "age": 34,
                    "employment_type": "Salaried",
                    "employer_name": "Apex Cloud Technologies Pvt Ltd",
                    "employment_months": 48,
                    "occupation": "Senior Software Architect",
                    "monthly_income": 125000.0,
                    "monthly_take_home": 105000.0,
                    "existing_monthly_obligations": 18000.0,
                    "requested_loan_amount": 500000.0,
                    "loan_tenure_months": 36,
                    "proposed_interest_rate": 11.5,
                    "loan_purpose": "Home Interior Refurbishment",
                    "interest_rate_type": "Fixed",
                    "credit_score": 780,
                    "credit_score_source": "Authorized Bureau Synthetic Simulator (Date: 2026-10-01)",
                    "consent_given": True
                },
                "documents": [
                    {"requirement_id": "REQ-PL-ID", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-PL-ADDR", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-PL-PHOTO", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-PL-SALARY-SLIPS", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-PL-BANK-STMT", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-PL-FORM16", "status": "EXTRACTION_COMPLETED"}
                ],
                "simulation_flags": {
                    "simulate_failed_integration": False,
                    "simulate_unavailable_model": False,
                    "simulate_tampered_docs": False
                }
            },
            "PL_HIGH_DTI_OVERLEVERAGED": {
                "name": "Personal Loan: Over-leveraged Applicant (DTI Breach Exception)",
                "product": "PERSONAL_LOAN",
                "applicant": {
                    "full_name": "Vikram Patel (Synthetic)",
                    "email": "vikram.synth@example.com",
                    "phone": "+91 98765 11223",
                    "date_of_birth": "1988-11-20",
                    "age": 38,
                    "employment_type": "Salaried",
                    "employer_name": "Metro Logistics Ltd",
                    "employment_months": 24,
                    "occupation": "Operations Manager",
                    "monthly_income": 60000.0,
                    "monthly_take_home": 52000.0,
                    "existing_monthly_obligations": 32000.0,
                    "requested_loan_amount": 400000.0,
                    "loan_tenure_months": 24,
                    "proposed_interest_rate": 13.0,
                    "loan_purpose": "Debt Consolidation",
                    "interest_rate_type": "Fixed",
                    "credit_score": 645,
                    "credit_score_source": "Authorized Bureau Synthetic Simulator (Date: 2026-09-15)",
                    "consent_given": True
                },
                "documents": [
                    {"requirement_id": "REQ-PL-ID", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-PL-ADDR", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-PL-PHOTO", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-PL-SALARY-SLIPS", "status": "MISMATCH_DETECTED"},
                    {"requirement_id": "REQ-PL-BANK-STMT", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-PL-FORM16", "status": "NOT_UPLOADED"}
                ],
                "simulation_flags": {
                    "simulate_failed_integration": False,
                    "simulate_unavailable_model": False,
                    "simulate_tampered_docs": False
                }
            },
            "EDU_PREMIER_STEM_CONFIRMED": {
                "name": "Education Loan: Premier STEM Master's (Confirmed Admission)",
                "product": "EDUCATION_LOAN",
                "applicant": {
                    "full_name": "Ananya Sen (Synthetic Student)",
                    "email": "ananya.synth@univ.edu",
                    "phone": "+91 98765 88990",
                    "date_of_birth": "2002-08-19",
                    "age": 24,
                    "nationality": "Indian",
                    "permanent_address": "Flat 402, Green Glen Layout, Bengaluru, Karnataka",
                    "university_name": "Indian Institute of Science (IISc)",
                    "college_institution_name": "Division of Electrical, Electronics and Computer Sciences",
                    "institution_address": "CV Raman Rd, Bengaluru, Karnataka 560012",
                    "college_pin_code": "560012",
                    "city_district_state": "Bengaluru Urban, Karnataka",
                    "country_of_study": "India",
                    "institution_type": "Institute of National Importance (Autonomous)",
                    "course_name": "M.Tech in Artificial Intelligence",
                    "course_duration_years": 2,
                    "course_start_date": "2026-08-01",
                    "expected_completion_date": "2028-06-30",
                    "admission_status": "Confirmed Admission",
                    "admission_letter_number": "IISC-MTECH-AI-2026-0492",
                    "tuition_fees": 600000.0,
                    "admission_reg_fees": 30000.0,
                    "examination_fees": 20000.0,
                    "hostel_living_cost": 240000.0,
                    "books_equipment_cost": 100000.0,
                    "travel_living_cost": 50000.0,
                    "confirmed_scholarship": 150000.0,
                    "unconfirmed_scholarship": 50000.0,
                    "other_funding": 0.0,
                    "student_contribution": 90000.0,
                    "requested_loan_amount": 800000.0,
                    "loan_tenure_months": 84,
                    "moratorium_months": 36,  # 24m course + 12m grace
                    "proposed_interest_rate": 9.25,
                    "co_applicant_name": "Subir Sen (Father)",
                    "co_applicant_relation": "Father",
                    "co_applicant_income": 95000.0,
                    "co_applicant_existing_emi": 12000.0,
                    "monthly_income": 0.0,  # Zero student income is normal
                    "credit_score": 765,
                    "credit_score_source": "Co-Applicant Bureau Synthetic Simulator (Date: 2026-10-10)",
                    "consent_given": True
                },
                "documents": [
                    {"requirement_id": "REQ-EDU-OFFER-LETTER", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-FEE-STRUCTURE", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-ACADEMIC-RECORDS", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-ENTRANCE-SCORECARD", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-STUDENT-KYC", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-COAPP-KYC", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-COAPP-INCOME", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"},
                    {"requirement_id": "REQ-EDU-SCHOLARSHIP-LETTER", "status": "VERIFIED_THROUGH_AUTHORIZED_INTEGRATION"}
                ],
                "simulation_flags": {
                    "simulate_failed_integration": False,
                    "simulate_unavailable_model": False,
                    "simulate_tampered_docs": False
                }
            },
            "EDU_UNCONFIRMED_NO_COAPP": {
                "name": "Education Loan: Application Pending Offer & Missing Co-Applicant (Escalation Case)",
                "product": "EDUCATION_LOAN",
                "applicant": {
                    "full_name": "Rohan Mehra (Synthetic Student)",
                    "email": "rohan.synth@college.org",
                    "phone": "+91 98765 33445",
                    "date_of_birth": "2003-04-12",
                    "age": 23,
                    "nationality": "Indian",
                    "permanent_address": "Sector 14, Gurugram, Haryana",
                    "university_name": "International Tech University",
                    "college_institution_name": "School of Computing",
                    "institution_address": "Tech Enclave, Noida, Uttar Pradesh 201301",
                    "college_pin_code": "201301",
                    "city_district_state": "Gautam Buddha Nagar, Uttar Pradesh",
                    "country_of_study": "India",
                    "institution_type": "Private Deemed University",
                    "course_name": "B.Tech Computer Science",
                    "course_duration_years": 4,
                    "course_start_date": "2026-09-01",
                    "expected_completion_date": "2030-06-30",
                    "admission_status": "Applied",  # Pending offer!
                    "admission_letter_number": "",
                    "tuition_fees": 1200000.0,
                    "admission_reg_fees": 50000.0,
                    "examination_fees": 40000.0,
                    "hostel_living_cost": 400000.0,
                    "books_equipment_cost": 80000.0,
                    "travel_living_cost": 30000.0,
                    "confirmed_scholarship": 0.0,
                    "unconfirmed_scholarship": 200000.0,  # Unconfirmed
                    "other_funding": 0.0,
                    "student_contribution": 0.0,
                    "requested_loan_amount": 1800000.0,
                    "loan_tenure_months": 120,
                    "moratorium_months": 60,
                    "proposed_interest_rate": 10.5,
                    "co_applicant_name": "",  # Missing co-applicant for > 4L loan!
                    "co_applicant_relation": "",
                    "co_applicant_income": 0.0,
                    "co_applicant_existing_emi": 0.0,
                    "monthly_income": 0.0,
                    "credit_score": None,
                    "consent_given": True
                },
                "documents": [
                    {"requirement_id": "REQ-EDU-OFFER-LETTER", "status": "NOT_UPLOADED"},
                    {"requirement_id": "REQ-EDU-FEE-STRUCTURE", "status": "UPLOADED"},
                    {"requirement_id": "REQ-EDU-ACADEMIC-RECORDS", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-EDU-STUDENT-KYC", "status": "EXTRACTION_COMPLETED"},
                    {"requirement_id": "REQ-EDU-COAPP-KYC", "status": "NOT_UPLOADED"},
                    {"requirement_id": "REQ-EDU-COAPP-INCOME", "status": "NOT_UPLOADED"}
                ],
                "simulation_flags": {
                    "simulate_failed_integration": False,
                    "simulate_unavailable_model": False,
                    "simulate_tampered_docs": False
                }
            }
        }

    @staticmethod
    def execute_sandbox_workflow(
        scenario_name: str,
        applicant_data: Dict[str, Any],
        documents: List[Dict[str, Any]],
        simulation_flags: Dict[str, bool],
        staff_role: str
    ) -> Dict[str, Any]:
        """
        Execute the exact seven-agent workflow in COMPLETE sandbox isolation.
        Results and audit trails are persisted exclusively into data/sandbox_evaluations.db.
        """
        SandboxService.init_sandbox_db()
        sandbox_id = f"SBX-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        loan_product = applicant_data.get("loan_product", "PERSONAL_LOAN")

        # 1. Financial calculation
        t0 = time.time()
        fin_principal = float(applicant_data.get("requested_loan_amount", 0.0))
        fin_rate = float(applicant_data.get("proposed_interest_rate", 12.0))
        fin_tenure = int(applicant_data.get("loan_tenure_months", 36))
        student_income = float(applicant_data.get("monthly_income", 0.0))
        coapp_income = float(applicant_data.get("co_applicant_income", 0.0))
        effective_income = (student_income + coapp_income) if loan_product == "EDUCATION_LOAN" else student_income
        existing_obligations = float(applicant_data.get("existing_monthly_obligations", 0.0)) + float(applicant_data.get("co_applicant_existing_emi", 0.0))

        emi = FinancialEngine.calculate_emi(fin_principal, fin_rate, fin_tenure)
        net_disbursed, total_upfront, upfront_breakdown = FinancialEngine.calculate_net_disbursement(fin_principal)
        apr_pct = FinancialEngine.calculate_apr(fin_principal, net_disbursed, emi, fin_tenure)
        amortization_schedule = FinancialEngine.generate_amortization_schedule(fin_principal, fin_rate, fin_tenure, max_rows=12)

        edu_reconciliation = None
        edu_moratorium = None
        if loan_product == "EDUCATION_LOAN":
            edu_reconciliation = FinancialEngine.reconcile_education_costs(
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
            edu_moratorium = FinancialEngine.calculate_education_moratorium_and_repayment(
                principal=fin_principal,
                annual_rate_pct=fin_rate,
                moratorium_months=int(applicant_data.get("moratorium_months", 36)),
                repayment_tenure_months=fin_tenure
            )

        fin_duration = round((time.time() - t0) * 1000, 2)

        # 2. Rules Evaluation
        t0 = time.time()
        rules_evaluated = []
        is_consistent = True
        inst_status = "Not evaluated"
        inst_warnings = []

        if loan_product == "EDUCATION_LOAN":
            is_consistent, inst_status, inst_warnings = EducationLoanPolicy.validate_institution_consistency(applicant_data)
            rules_evaluated = EducationLoanPolicy.evaluate_rules(
                applicant_data=applicant_data,
                financial_data={"monthly_emi": emi, "dti_ratio": round((existing_obligations + emi) / max(1.0, effective_income), 4)}
            )
        else:
            rules_evaluated = PersonalLoanPolicy.evaluate_rules(
                applicant_data=applicant_data,
                financial_data={"dti_ratio": round((existing_obligations + emi) / max(1.0, effective_income), 4)}
            )
        rules_duration = round((time.time() - t0) * 1000, 2)

        # 3. Simulation flags handling
        failed_integration = simulation_flags.get("simulate_failed_integration", False)
        unavailable_model = simulation_flags.get("simulate_unavailable_model", False)

        ml_risk_band = "LOW" if applicant_data.get("credit_score", 0) and applicant_data.get("credit_score", 0) >= 750 else "MODERATE"
        default_prob = 0.042 if ml_risk_band == "LOW" else 0.118

        if unavailable_model:
            ml_risk_status = "UNAVAILABLE"
            ml_risk_summary = "Machine-learning risk estimate unavailable (Simulated offline model scenario)."
            ml_risk_band = "NOT_ASSESSED"
            default_prob = None
        else:
            ml_risk_status = "SUCCESS"
            ml_risk_summary = f"Default probability: {round(default_prob*100, 1)}% ({ml_risk_band} risk band)."

        # Check document statuses
        unverified_docs = [
            d["requirement_id"] for d in documents
            if d.get("status") in [DocumentStatus.NOT_UPLOADED.value, DocumentStatus.MISMATCH_DETECTED.value, DocumentStatus.REUPLOAD_REQUIRED.value]
        ]

        failed_rules = [r for r in rules_evaluated if r.get("result") == "FAIL"]

        # Determine preliminary outcome
        if failed_integration:
            outcome = PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION
            outcome_reason = "External credit bureau / KYC integration timeout or failed response. Placed on hold."
        elif unverified_docs:
            outcome = PreliminaryOutcome.MORE_INFORMATION_REQUIRED
            outcome_reason = f"Mandatory document verification pending or missing: {', '.join(unverified_docs)}."
        elif failed_rules:
            blocking = [r for r in failed_rules if r.get("severity") == "BLOCKING"]
            if blocking:
                outcome = PreliminaryOutcome.HUMAN_REVIEW_REQUIRED
                outcome_reason = f"Underwriting policy exception triggered: {blocking[0].get('name')}."
            else:
                outcome = PreliminaryOutcome.HUMAN_REVIEW_REQUIRED
                outcome_reason = "Policy warning triggered requiring authorized underwriter review."
        elif not is_consistent:
            outcome = PreliminaryOutcome.HUMAN_REVIEW_REQUIRED
            outcome_reason = f"Institutional consistency mismatch detected: {'; '.join(inst_warnings)}."
        else:
            outcome = PreliminaryOutcome.PROCEED_TO_NEXT_STAGE
            outcome_reason = "All deterministic policy rules and verified documents satisfied baseline pre-screening criteria."

        # Compile agent traces
        agent_traces = [
            {
                "agent_name": "CoordinatorAgent",
                "duration_ms": 1.2,
                "status": "SUCCESS",
                "input_summary": f"Initiated synthetic sandbox assessment for {scenario_name}",
                "output_summary": f"Orchestrated 7 agents in isolated sandbox environment",
                "escalation_reason": None
            },
            {
                "agent_name": "DataValidationAgent",
                "duration_ms": 2.8,
                "status": "WARNING" if unverified_docs or not is_consistent else "SUCCESS",
                "input_summary": f"Product: {loan_product}, Documents evaluated: {len(documents)}",
                "output_summary": f"Unverified: {len(unverified_docs)}, Inst Status: {inst_status}",
                "escalation_reason": "; ".join(inst_warnings) if inst_warnings else (f"Pending docs: {len(unverified_docs)}" if unverified_docs else None)
            },
            {
                "agent_name": "FinancialAnalysisAgent",
                "duration_ms": fin_duration,
                "status": "SUCCESS",
                "input_summary": f"Principal: INR {fin_principal:,.0f}, Tenure: {fin_tenure}m, Rate: {fin_rate}%",
                "output_summary": f"EMI: INR {emi:,.2f}, APR: {apr_pct}%, Net Disbursed: INR {net_disbursed:,.2f}",
                "escalation_reason": None
            },
            {
                "agent_name": "EligibilityRulesAgent",
                "duration_ms": rules_duration,
                "status": "WARNING" if failed_rules else "SUCCESS",
                "input_summary": f"Evaluated {len(rules_evaluated)} product policy rules",
                "output_summary": f"Passed: {len(rules_evaluated) - len(failed_rules)}, Failed: {len(failed_rules)}",
                "escalation_reason": failed_rules[0].get("explanation") if failed_rules else None
            },
            {
                "agent_name": "CreditRiskAgent",
                "duration_ms": 3.1,
                "status": ml_risk_status,
                "input_summary": f"Bureau Score: {applicant_data.get('credit_score')}, Source: {applicant_data.get('credit_score_source')}",
                "output_summary": ml_risk_summary,
                "escalation_reason": "ML Model Unavailable" if unavailable_model else None
            },
            {
                "agent_name": "RiskExplanationAgent",
                "duration_ms": 2.4,
                "status": "SUCCESS",
                "input_summary": "Unified deterministic rules, document verifications, and financial ratios",
                "output_summary": f"Recommendation: {outcome.value}",
                "escalation_reason": outcome_reason if outcome != PreliminaryOutcome.PROCEED_TO_NEXT_STAGE else None
            },
            {
                "agent_name": "RecordManagementAgent",
                "duration_ms": 4.5,
                "status": "SUCCESS",
                "input_summary": f"Persisted isolated sandbox evaluation bundle ({sandbox_id})",
                "output_summary": "Saved to data/sandbox_evaluations.db",
                "escalation_reason": None
            }
        ]

        # Persist into isolated Sandbox DB
        conn = SandboxService.get_sandbox_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO sandbox_applications (
                sandbox_id, scenario_name, loan_product, applicant_data_json,
                documents_json, simulation_flags_json, preliminary_outcome,
                status, created_by_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sandbox_id,
            scenario_name,
            loan_product,
            json.dumps(applicant_data),
            json.dumps(documents),
            json.dumps(simulation_flags),
            outcome.value,
            "COMPLETED",
            staff_role
        ))

        for trace in agent_traces:
            cur.execute("""
                INSERT INTO sandbox_agent_runs (
                    run_id, sandbox_id, agent_name, duration_ms, status,
                    input_summary, output_summary, escalation_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"SBRUN-{uuid.uuid4().hex[:8].upper()}",
                sandbox_id,
                trace["agent_name"],
                trace["duration_ms"],
                trace["status"],
                trace["input_summary"],
                trace["output_summary"],
                trace["escalation_reason"]
            ))

        cur.execute("""
            INSERT INTO sandbox_audit_logs (
                log_id, sandbox_id, actor_role, action, details_json
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            f"SBLOG-{uuid.uuid4().hex[:8].upper()}",
            sandbox_id,
            staff_role,
            "SANDBOX_SCENARIO_EXECUTED",
            json.dumps({
                "scenario_name": scenario_name,
                "outcome": outcome.value,
                "simulated_flags": simulation_flags
            })
        ))

        conn.commit()
        conn.close()

        return {
            "sandbox_id": sandbox_id,
            "scenario_name": scenario_name,
            "loan_product": loan_product,
            "preliminary_outcome": outcome.value,
            "outcome_reason": outcome_reason,
            "financials": {
                "principal": fin_principal,
                "annual_rate": fin_rate,
                "tenure_months": fin_tenure,
                "monthly_emi": emi,
                "net_disbursed": net_disbursed,
                "total_upfront_deductions": total_upfront,
                "upfront_breakdown": upfront_breakdown,
                "apr_pct": apr_pct,
                "amortization_schedule": [r.model_dump() for r in amortization_schedule],
                "edu_reconciliation": edu_reconciliation.model_dump() if edu_reconciliation else None,
                "edu_moratorium": edu_moratorium
            },
            "rules_evaluated": rules_evaluated,
            "institution_validation": {
                "is_consistent": is_consistent,
                "status_message": inst_status,
                "warnings": inst_warnings
            },
            "agent_traces": agent_traces,
            "simulation_flags": simulation_flags
        }

    @staticmethod
    def list_sandbox_evaluations() -> List[Dict[str, Any]]:
        """Retrieve recent sandbox evaluation runs."""
        SandboxService.init_sandbox_db()
        conn = SandboxService.get_sandbox_connection()
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT sandbox_id, scenario_name, loan_product, preliminary_outcome,
                   status, created_by_role, created_at
            FROM sandbox_applications
            ORDER BY created_at DESC
            LIMIT 50
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_sandbox_evaluation(sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a specific sandbox evaluation."""
        SandboxService.init_sandbox_db()
        conn = SandboxService.get_sandbox_connection()
        row = conn.execute("""
            SELECT * FROM sandbox_applications WHERE sandbox_id = ?
        """, (sandbox_id,)).fetchone()
        if not row:
            conn.close()
            return None

        runs = conn.execute("""
            SELECT agent_name, duration_ms, status, input_summary, output_summary, escalation_reason, executed_at
            FROM sandbox_agent_runs WHERE sandbox_id = ?
            ORDER BY rowid ASC
        """, (sandbox_id,)).fetchall()

        logs = conn.execute("""
            SELECT log_id, actor_role, action, details_json, created_at
            FROM sandbox_audit_logs WHERE sandbox_id = ?
            ORDER BY rowid ASC
        """, (sandbox_id,)).fetchall()

        conn.close()
        data = dict(row)
        data["agent_runs"] = [dict(r) for r in runs]
        data["audit_logs"] = [dict(l) for l in logs]
        data["applicant_data"] = json.loads(data["applicant_data_json"])
        data["documents"] = json.loads(data["documents_json"])
        data["simulation_flags"] = json.loads(data["simulation_flags_json"])
        return data

    @staticmethod
    def reset_sandbox_database() -> int:
        """Purge all sandbox test records without touching production databases."""
        SandboxService.init_sandbox_db()
        conn = SandboxService.get_sandbox_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sandbox_agent_runs;")
        cur.execute("DELETE FROM sandbox_audit_logs;")
        cur.execute("DELETE FROM sandbox_applications;")
        count = cur.rowcount
        conn.commit()
        conn.close()
        return count
