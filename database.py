"""
SQLite Database service with normalized tables, parameterized queries, and audit tracking.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from config.settings import DB_PATH

logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    """Return a configured SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Create all required normalized tables and indexes if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    -- Applicants Table (Personal baseline data)
    CREATE TABLE IF NOT EXISTS applicants (
        applicant_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        age INTEGER NOT NULL,
        employment_type TEXT NOT NULL,
        employment_months INTEGER DEFAULT 0,
        monthly_income REAL NOT NULL,
        existing_monthly_obligations REAL DEFAULT 0.0,
        dependents INTEGER DEFAULT 0,
        national_id_masked TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Applications Table (Core workflow states)
    CREATE TABLE IF NOT EXISTS applications (
        application_id TEXT PRIMARY KEY,
        applicant_id TEXT NOT NULL,
        loan_product TEXT NOT NULL,
        requested_loan_amount REAL NOT NULL,
        loan_tenure_months INTEGER NOT NULL,
        proposed_interest_rate REAL NOT NULL,
        credit_score INTEGER,
        previous_defaults_count INTEGER DEFAULT 0,
        consent_given INTEGER NOT NULL,
        status TEXT NOT NULL,
        preliminary_outcome TEXT,
        assigned_to TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id)
    );

    -- Documents Table
    CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        doc_category TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        status TEXT NOT NULL,
        extracted_fields_json TEXT,
        confirmed_by_applicant INTEGER DEFAULT 0,
        verification_notes TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Agent Run Logs Table
    CREATE TABLE IF NOT EXISTS agent_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        workflow_trace_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration_ms REAL NOT NULL,
        status TEXT NOT NULL,
        input_summary TEXT,
        output_summary TEXT,
        escalation_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Validation Results
    CREATE TABLE IF NOT EXISTS validation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        is_valid INTEGER NOT NULL,
        blocking_errors_json TEXT,
        warnings_json TEXT,
        missing_fields_json TEXT,
        duplicate_flags_json TEXT,
        inconsistency_flags_json TEXT,
        recommended_action TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Financial Assessments
    CREATE TABLE IF NOT EXISTS financial_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        monthly_emi REAL NOT NULL,
        existing_obligations REAL NOT NULL,
        total_monthly_obligations REAL NOT NULL,
        dti_ratio REAL NOT NULL,
        loan_to_annual_income REAL NOT NULL,
        net_disposable_income REAL NOT NULL,
        assumptions_json TEXT,
        warnings_json TEXT,
        is_reliable INTEGER NOT NULL,
        calculation_explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Rule Evaluations
    CREATE TABLE IF NOT EXISTS rule_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        rules_evaluated INTEGER NOT NULL,
        rules_passed INTEGER NOT NULL,
        rules_failed INTEGER NOT NULL,
        requires_human_review INTEGER NOT NULL,
        summary TEXT,
        rule_items_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Risk Assessments (ML Agent)
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        risk_score REAL,
        risk_category TEXT NOT NULL,
        model_version TEXT NOT NULL,
        model_name TEXT NOT NULL,
        features_used_json TEXT,
        is_prediction_reliable INTEGER NOT NULL,
        limitations_json TEXT,
        warnings_json TEXT,
        explanation_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Recommendations (Explanation Agent)
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT NOT NULL,
        preliminary_outcome TEXT NOT NULL,
        positive_factors_json TEXT,
        negative_factors_json TEXT,
        evidence_trail_json TEXT,
        human_review_summary TEXT,
        pause_reason TEXT,
        escalation_flags_json TEXT,
        disclaimer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Human Reviews Table
    CREATE TABLE IF NOT EXISTS human_reviews (
        review_id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        reviewer_name TEXT NOT NULL,
        role TEXT NOT NULL,
        decision TEXT NOT NULL,
        findings TEXT NOT NULL,
        conditions TEXT,
        decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Fraud Cases Table
    CREATE TABLE IF NOT EXISTS fraud_cases (
        case_id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        triggering_flags_json TEXT NOT NULL,
        evidence_notes TEXT,
        investigator_id TEXT,
        status TEXT NOT NULL, -- OPEN, UNDER_INVESTIGATION, CLEARED, CONFIRMED_FRAUD
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id)
    );

    -- Complaints & Disputes Table
    CREATE TABLE IF NOT EXISTS complaints_disputes (
        case_id TEXT PRIMARY KEY,
        application_id TEXT,
        applicant_name TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        category TEXT NOT NULL, -- DISPUTED_CREDIT_INFO, IDENTITY_THEFT, INCORRECT_DATA, DISPUTED_EXPLANATION, OTHER
        priority TEXT NOT NULL, -- LOW, MEDIUM, HIGH, URGENT
        description TEXT NOT NULL,
        status TEXT NOT NULL, -- OPEN, ASSIGNED, UNDER_REVIEW, RESOLVED, CLOSED
        assigned_reviewer TEXT,
        resolution_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    );

    -- Audit Logs Table
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        event_details_json TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Notifications Table
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT,
        recipient TEXT NOT NULL,
        channel TEXT NOT NULL, -- EMAIL, SMS, SYSTEM
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL, -- SENT_SIMULATED, FAILED
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Model Versions
    CREATE TABLE IF NOT EXISTS model_versions (
        version_id TEXT PRIMARY KEY,
        algorithm TEXT NOT NULL,
        training_date TEXT NOT NULL,
        metrics_json TEXT NOT NULL,
        features_json TEXT NOT NULL,
        is_active INTEGER DEFAULT 0
    );

    -- Integration Events Table
    CREATE TABLE IF NOT EXISTS integration_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        mode TEXT NOT NULL, -- SIMULATED, LIVE
        request_summary TEXT,
        response_status TEXT NOT NULL,
        duration_ms REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Indexes for high-performance filtering and search
    CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status);
    CREATE INDEX IF NOT EXISTS idx_apps_applicant ON applications(applicant_id);
    CREATE INDEX IF NOT EXISTS idx_docs_app ON documents(application_id);
    CREATE INDEX IF NOT EXISTS idx_agent_runs_app ON agent_runs(application_id);
    CREATE INDEX IF NOT EXISTS idx_audit_app ON audit_logs(application_id);
    CREATE INDEX IF NOT EXISTS idx_fraud_status ON fraud_cases(status);
    CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints_disputes(status);
    """)

    conn.commit()
    conn.close()


# --- Application Queries ---

def create_initial_application(applicant_data: Dict[str, Any], application_id: str, trace_id: str = "TRC-INITIAL") -> bool:
    """Create initial placeholder applicant and application record in SQLite upon arrival."""
    conn = get_db_connection()
    try:
        with conn:
            applicant_id = applicant_data.get("applicant_id") or f"AP-{application_id}"
            conn.execute("""
            INSERT OR REPLACE INTO applicants (
                applicant_id, full_name, email, phone, date_of_birth, age,
                employment_type, employment_months, monthly_income,
                existing_monthly_obligations, dependents, national_id_masked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                applicant_id,
                applicant_data.get("full_name") or "New Applicant",
                applicant_data.get("email") or "applicant@example.com",
                applicant_data.get("phone") or "0000000000",
                applicant_data.get("date_of_birth") or "1990-01-01",
                int(applicant_data.get("age") or 25),
                applicant_data.get("employment_type") or "Salaried Full-Time",
                int(applicant_data.get("employment_months") or 0),
                float(applicant_data.get("monthly_income") or 0.0),
                float(applicant_data.get("existing_monthly_obligations") or 0.0),
                int(applicant_data.get("dependents") or 0),
                applicant_data.get("national_id_number") or "MASKED-XXXX"
            ))

            conn.execute("""
            INSERT OR REPLACE INTO applications (
                application_id, applicant_id, loan_product, requested_loan_amount,
                loan_tenure_months, proposed_interest_rate, credit_score,
                previous_defaults_count, consent_given, status, preliminary_outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                applicant_id,
                applicant_data.get("loan_product") or "PERSONAL_LOAN",
                float(applicant_data.get("requested_loan_amount") or 0.0),
                int(applicant_data.get("loan_tenure_months") or 12),
                float(applicant_data.get("proposed_interest_rate") or 12.0),
                applicant_data.get("credit_score"),
                int(applicant_data.get("previous_defaults_count") or 0),
                1 if applicant_data.get("consent_given", True) else 0,
                "RECEIVED",
                "UNDER_EVALUATION"
            ))
        return True
    except Exception as e:
        logger.error(f"Error creating initial application record: {e}")
        return False
    finally:
        conn.close()

def save_application_bundle(
    applicant_data: Dict[str, Any],
    app_data: Dict[str, Any],
    validation_res: Optional[Dict[str, Any]] = None,
    financial_res: Optional[Dict[str, Any]] = None,
    rules_res: Optional[Dict[str, Any]] = None,
    risk_res: Optional[Dict[str, Any]] = None,
    rec_res: Optional[Dict[str, Any]] = None,
    agent_logs: Optional[List[Dict[str, Any]]] = None,
    trace_id: str = "TRC-DEFAULT"
) -> bool:
    """Save an entire application bundle inside a transactional SQLite block."""
    conn = get_db_connection()
    try:
        with conn:
            # 1. Insert or update applicant
            conn.execute("""
            INSERT OR REPLACE INTO applicants (
                applicant_id, full_name, email, phone, date_of_birth, age,
                employment_type, employment_months, monthly_income,
                existing_monthly_obligations, dependents, national_id_masked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                applicant_data.get("applicant_id") or f"AP-{app_data.get('application_id')}",
                applicant_data.get("full_name") or "Applicant",
                applicant_data.get("email") or "applicant@example.com",
                applicant_data.get("phone") or "0000000000",
                applicant_data.get("date_of_birth") or "1990-01-01",
                int(applicant_data.get("age") or 25),
                applicant_data.get("employment_type") or "Salaried Full-Time",
                int(applicant_data.get("employment_months") or 0),
                float(applicant_data.get("monthly_income") or 0.0),
                float(applicant_data.get("existing_monthly_obligations") or 0.0),
                int(applicant_data.get("dependents") or 0),
                applicant_data.get("national_id_number") or "MASKED-XXXX"
            ))

            # 2. Insert or update application
            conn.execute("""
            INSERT OR REPLACE INTO applications (
                application_id, applicant_id, loan_product, requested_loan_amount,
                loan_tenure_months, proposed_interest_rate, credit_score,
                previous_defaults_count, consent_given, status, preliminary_outcome,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                app_data["application_id"],
                applicant_data["applicant_id"],
                app_data["loan_product"],
                app_data["requested_loan_amount"],
                app_data["loan_tenure_months"],
                app_data["proposed_interest_rate"],
                app_data.get("credit_score"),
                app_data.get("previous_defaults_count", 0),
                1 if app_data.get("consent_given", True) else 0,
                app_data["status"],
                app_data.get("preliminary_outcome")
            ))

            app_id = app_data["application_id"]

            # 3. Validation result
            if validation_res:
                conn.execute("""
                INSERT INTO validation_results (
                    application_id, is_valid, blocking_errors_json, warnings_json,
                    missing_fields_json, duplicate_flags_json, inconsistency_flags_json,
                    recommended_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_id,
                    1 if validation_res.get("is_valid") else 0,
                    json.dumps(validation_res.get("blocking_errors", [])),
                    json.dumps(validation_res.get("warnings", [])),
                    json.dumps(validation_res.get("missing_fields", [])),
                    json.dumps(validation_res.get("duplicate_flags", [])),
                    json.dumps(validation_res.get("inconsistency_flags", [])),
                    validation_res.get("recommended_action", "PROCEED")
                ))

            # 4. Financial assessment
            if financial_res:
                conn.execute("""
                INSERT INTO financial_assessments (
                    application_id, monthly_emi, existing_obligations,
                    total_monthly_obligations, dti_ratio, loan_to_annual_income,
                    net_disposable_income, assumptions_json, warnings_json,
                    is_reliable, calculation_explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_id,
                    financial_res.get("monthly_emi", 0.0),
                    financial_res.get("existing_obligations", 0.0),
                    financial_res.get("total_monthly_obligations", 0.0),
                    financial_res.get("dti_ratio", 0.0),
                    financial_res.get("loan_to_annual_income", 0.0),
                    financial_res.get("net_disposable_income", 0.0),
                    json.dumps(financial_res.get("assumptions", {})),
                    json.dumps(financial_res.get("warnings", [])),
                    1 if financial_res.get("is_reliable", True) else 0,
                    financial_res.get("calculation_explanation", "")
                ))

            # 5. Rule evaluations
            if rules_res:
                conn.execute("""
                INSERT INTO rule_evaluations (
                    application_id, rules_evaluated, rules_passed, rules_failed,
                    requires_human_review, summary, rule_items_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_id,
                    rules_res.get("rules_evaluated", 0),
                    rules_res.get("rules_passed", 0),
                    rules_res.get("rules_failed", 0),
                    1 if rules_res.get("requires_human_review") else 0,
                    rules_res.get("summary", ""),
                    json.dumps(rules_res.get("rule_items", []))
                ))

            # 6. Risk assessment
            if risk_res:
                conn.execute("""
                INSERT INTO risk_assessments (
                    application_id, risk_score, risk_category, model_version,
                    model_name, features_used_json, is_prediction_reliable,
                    limitations_json, warnings_json, explanation_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_id,
                    risk_res.get("risk_score"),
                    risk_res.get("risk_category", "UNCERTAIN"),
                    risk_res.get("model_version", "v1.0-academic"),
                    risk_res.get("model_name", "RandomForestClassifier"),
                    json.dumps(risk_res.get("features_used", [])),
                    1 if risk_res.get("is_prediction_reliable", True) else 0,
                    json.dumps(risk_res.get("limitations", [])),
                    json.dumps(risk_res.get("warnings", [])),
                    risk_res.get("explanation_notes", "")
                ))

            # 7. Recommendations
            if rec_res:
                conn.execute("""
                INSERT INTO recommendations (
                    application_id, preliminary_outcome, positive_factors_json,
                    negative_factors_json, evidence_trail_json, human_review_summary,
                    pause_reason, escalation_flags_json, disclaimer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_id,
                    rec_res.get("preliminary_outcome", "REQUIRES_HUMAN_REVIEW"),
                    json.dumps(rec_res.get("positive_factors", [])),
                    json.dumps(rec_res.get("negative_factors", [])),
                    json.dumps(rec_res.get("evidence_trail", [])),
                    rec_res.get("human_review_summary"),
                    rec_res.get("pause_reason"),
                    json.dumps(rec_res.get("escalation_flags", [])),
                    rec_res.get("disclaimer", "")
                ))

            # 8. Agent Run Logs
            if agent_logs:
                for log in agent_logs:
                    conn.execute("""
                    INSERT INTO agent_runs (
                        application_id, workflow_trace_id, agent_name, start_time,
                        end_time, duration_ms, status, input_summary, output_summary,
                        escalation_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app_id,
                        trace_id,
                        log.get("agent_name", "UnknownAgent"),
                        log.get("start_time", ""),
                        log.get("end_time", ""),
                        log.get("duration_ms", 0.0),
                        log.get("status", "SUCCESS"),
                        log.get("input_summary", ""),
                        log.get("output_summary", ""),
                        log.get("escalation_reason")
                    ))

            # 9. Audit Log
            conn.execute("""
            INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
            VALUES (?, ?, ?, ?, ?)
            """, (
                app_id,
                "SYSTEM_COORDINATOR",
                "ORCHESTRATOR",
                "ASSESSMENT_COMPLETED",
                json.dumps({"status": app_data["status"], "outcome": app_data.get("preliminary_outcome")})
            ))

        return True
    except Exception as e:
        logger.error(f"Error saving application bundle: {e}")
        return False
    finally:
        conn.close()


def get_dashboard_metrics() -> Dict[str, Any]:
    """Calculate dynamic metrics from SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_apps = cursor.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    auto_passed = cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE preliminary_outcome = 'PROCEED_TO_NEXT_STAGE'"
    ).fetchone()[0]
    review_required = cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE preliminary_outcome = 'REQUIRES_HUMAN_REVIEW' OR status = 'HUMAN_REVIEW_REQUIRED'"
    ).fetchone()[0]
    more_info = cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE preliminary_outcome = 'MORE_INFORMATION_REQUIRED' OR status = 'MORE_INFORMATION_REQUIRED'"
    ).fetchone()[0]
    fraud_cases = cursor.execute(
        "SELECT COUNT(*) FROM fraud_cases WHERE status != 'CLEARED'"
    ).fetchone()[0]
    complaints_open = cursor.execute(
        "SELECT COUNT(*) FROM complaints_disputes WHERE status != 'RESOLVED' AND status != 'CLOSED'"
    ).fetchone()[0]
    agent_exceptions = cursor.execute(
        "SELECT COUNT(*) FROM agent_runs WHERE status = 'ERROR'"
    ).fetchone()[0]

    # Average assessment time
    avg_duration_row = cursor.execute(
        "SELECT AVG(duration_ms) FROM agent_runs"
    ).fetchone()
    avg_assessment_ms = avg_duration_row[0] if avg_duration_row and avg_duration_row[0] else 0.0

    # Status distribution
    status_counts = cursor.execute(
        "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
    ).fetchall()
    status_dist = {row["status"]: row["count"] for row in status_counts}

    # Outcome distribution
    outcome_counts = cursor.execute(
        "SELECT preliminary_outcome, COUNT(*) as count FROM applications WHERE preliminary_outcome IS NOT NULL GROUP BY preliminary_outcome"
    ).fetchall()
    outcome_dist = {row["preliminary_outcome"]: row["count"] for row in outcome_counts}

    # Product distribution & loan volumes
    product_counts = cursor.execute("""
        SELECT loan_product, COUNT(*) as count, SUM(requested_loan_amount) as total_volume
        FROM applications
        GROUP BY loan_product
    """).fetchall()
    product_dist = {
        row["loan_product"]: {
            "count": row["count"],
            "total_volume": row["total_volume"] or 0.0
        }
        for row in product_counts
    }

    # Recent applications
    recent_apps = cursor.execute("""
        SELECT a.application_id, ap.full_name, a.loan_product, a.requested_loan_amount,
               a.status, a.preliminary_outcome, a.created_at
        FROM applications a
        JOIN applicants ap ON a.applicant_id = ap.applicant_id
        ORDER BY a.created_at DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return {
        "total_applications": total_apps,
        "auto_proceeded": auto_passed,
        "requiring_human_review": review_required,
        "more_info_required": more_info,
        "fraud_cases": fraud_cases,
        "open_complaints": complaints_open,
        "agent_exceptions": agent_exceptions,
        "avg_assessment_ms": round(avg_assessment_ms, 2),
        "status_distribution": status_dist,
        "outcome_distribution": outcome_dist,
        "product_distribution": product_dist,
        "recent_applications": [dict(r) for r in recent_apps]
    }


def list_applications(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    outcome_filter: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve filtered list of applications with applicant details."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT a.application_id, a.loan_product, a.requested_loan_amount,
               a.loan_tenure_months, a.status, a.preliminary_outcome,
               a.created_at, ap.applicant_id, ap.full_name, ap.email, ap.phone,
               ap.monthly_income, a.credit_score
        FROM applications a
        JOIN applicants ap ON a.applicant_id = ap.applicant_id
        WHERE 1=1
    """
    params: List[Any] = []

    if search:
        query += " AND (a.application_id LIKE ? OR ap.full_name LIKE ? OR ap.email LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])

    if status_filter and status_filter != "ALL":
        query += " AND a.status = ?"
        params.append(status_filter)

    if outcome_filter and outcome_filter != "ALL":
        query += " AND a.preliminary_outcome = ?"
        params.append(outcome_filter)

    query += " ORDER BY a.created_at DESC LIMIT ?"
    params.append(limit)

    rows = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_application_details(application_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete application details including outputs of all 7 agents."""
    conn = get_db_connection()
    cursor = conn.cursor()

    app_row = cursor.execute("""
        SELECT a.*, ap.full_name, ap.email, ap.phone, ap.date_of_birth, ap.age,
               ap.employment_type, ap.employment_months, ap.monthly_income,
               ap.existing_monthly_obligations, ap.dependents
        FROM applications a
        JOIN applicants ap ON a.applicant_id = ap.applicant_id
        WHERE a.application_id = ?
    """, (application_id,)).fetchone()

    if not app_row:
        conn.close()
        return None

    res = dict(app_row)

    # Fetch agent outputs
    val_row = cursor.execute(
        "SELECT * FROM validation_results WHERE application_id = ? ORDER BY id DESC LIMIT 1",
        (application_id,)
    ).fetchone()
    res["validation_result"] = dict(val_row) if val_row else None

    fin_row = cursor.execute(
        "SELECT * FROM financial_assessments WHERE application_id = ? ORDER BY id DESC LIMIT 1",
        (application_id,)
    ).fetchone()
    res["financial_result"] = dict(fin_row) if fin_row else None

    rule_row = cursor.execute(
        "SELECT * FROM rule_evaluations WHERE application_id = ? ORDER BY id DESC LIMIT 1",
        (application_id,)
    ).fetchone()
    res["rule_result"] = dict(rule_row) if rule_row else None

    risk_row = cursor.execute(
        "SELECT * FROM risk_assessments WHERE application_id = ? ORDER BY id DESC LIMIT 1",
        (application_id,)
    ).fetchone()
    res["risk_result"] = dict(risk_row) if risk_row else None

    rec_row = cursor.execute(
        "SELECT * FROM recommendations WHERE application_id = ? ORDER BY id DESC LIMIT 1",
        (application_id,)
    ).fetchone()
    res["recommendation_result"] = dict(rec_row) if rec_row else None

    # Fetch agent logs
    agent_logs = cursor.execute(
        "SELECT * FROM agent_runs WHERE application_id = ? ORDER BY run_id ASC",
        (application_id,)
    ).fetchall()
    res["agent_runs"] = [dict(r) for r in agent_logs]

    # Fetch documents
    docs = cursor.execute(
        "SELECT * FROM documents WHERE application_id = ?",
        (application_id,)
    ).fetchall()
    res["documents"] = [dict(d) for d in docs]

    # Fetch audit logs
    audits = cursor.execute(
        "SELECT * FROM audit_logs WHERE application_id = ? ORDER BY timestamp DESC",
        (application_id,)
    ).fetchall()
    res["audit_logs"] = [dict(a) for a in audits]

    # Fetch human review
    reviews = cursor.execute(
        "SELECT * FROM human_reviews WHERE application_id = ? ORDER BY decision_timestamp DESC",
        (application_id,)
    ).fetchall()
    res["human_reviews"] = [dict(hr) for hr in reviews]

    conn.close()
    return res


def record_human_review(
    application_id: str,
    reviewer_id: str,
    reviewer_name: str,
    role: str,
    decision: str,
    findings: str,
    conditions: str = ""
) -> bool:
    """Record an authorized human reviewer's final decision separately from AI advice."""
    conn = get_db_connection()
    try:
        import uuid
        review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        with conn:
            conn.execute("""
            INSERT INTO human_reviews (
                review_id, application_id, reviewer_id, reviewer_name, role,
                decision, findings, conditions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, application_id, reviewer_id, reviewer_name, role,
                decision, findings, conditions
            ))

            # Update application status based on human decision
            new_status = (
                "APPROVED_BY_AUTHORIZED_LENDER" if decision == "APPROVE"
                else "DECLINED_BY_AUTHORIZED_LENDER" if decision == "DECLINE"
                else "MORE_INFORMATION_REQUIRED" if decision == "REQUEST_INFO"
                else "HUMAN_REVIEW_REQUIRED"
            )

            conn.execute("""
            UPDATE applications
            SET status = ?, assigned_to = ?, updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
            """, (new_status, reviewer_name, application_id))

            conn.execute("""
            INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
            VALUES (?, ?, ?, ?, ?)
            """, (
                application_id,
                reviewer_id,
                role,
                "HUMAN_DECISION_RECORDED",
                json.dumps({"decision": decision, "review_id": review_id, "findings": findings})
            ))
        return True
    except Exception as e:
        logger.error(f"Error recording human review: {e}")
        return False
    finally:
        conn.close()


def create_fraud_case(
    application_id: str,
    triggering_flags: List[str],
    evidence_notes: str,
    investigator_id: Optional[str] = None
) -> str:
    """Open a dedicated fraud investigation case for suspicious indicators."""
    conn = get_db_connection()
    import uuid
    case_id = f"FRD-{uuid.uuid4().hex[:8].upper()}"
    try:
        with conn:
            conn.execute("""
            INSERT INTO fraud_cases (
                case_id, application_id, triggering_flags_json, evidence_notes,
                investigator_id, status
            ) VALUES (?, ?, ?, ?, ?, 'OPEN')
            """, (
                case_id, application_id, json.dumps(triggering_flags), evidence_notes, investigator_id
            ))

            conn.execute("""
            UPDATE applications
            SET status = 'ON_HOLD', updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
            """, (application_id,))

            conn.execute("""
            INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
            VALUES (?, ?, ?, ?, ?)
            """, (
                application_id,
                "FRAUD_DETECTION_ENGINE",
                "SECURITY",
                "FRAUD_CASE_OPENED",
                json.dumps({"case_id": case_id, "flags": triggering_flags})
            ))
        return case_id
    finally:
        conn.close()


def list_fraud_cases() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT f.*, ap.full_name, a.loan_product, a.requested_loan_amount
        FROM fraud_cases f
        JOIN applications a ON f.application_id = a.application_id
        JOIN applicants ap ON a.applicant_id = ap.applicant_id
        ORDER BY f.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_fraud_case(case_id: str, status: str, resolution_notes: str, investigator_id: str) -> bool:
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
            UPDATE fraud_cases
            SET status = ?, resolution_notes = ?, investigator_id = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE case_id = ?
            """, (status, resolution_notes, investigator_id, case_id))

            row = conn.execute("SELECT application_id FROM fraud_cases WHERE case_id = ?", (case_id,)).fetchone()
            if row:
                app_id = row["application_id"]
                conn.execute("""
                INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    app_id,
                    investigator_id,
                    "FRAUD_INVESTIGATOR",
                    "FRAUD_CASE_RESOLVED",
                    json.dumps({"case_id": case_id, "status": status, "resolution": resolution_notes})
                ))
        return True
    finally:
        conn.close()


def create_complaint_case(
    application_id: Optional[str],
    applicant_name: str,
    contact_info: str,
    category: str,
    priority: str,
    description: str
) -> str:
    """Open a dispute or grievance ticket."""
    conn = get_db_connection()
    import uuid
    case_id = f"DISP-{uuid.uuid4().hex[:8].upper()}"
    try:
        with conn:
            conn.execute("""
            INSERT INTO complaints_disputes (
                case_id, application_id, applicant_name, contact_info,
                category, priority, description, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """, (
                case_id, application_id, applicant_name, contact_info,
                category, priority, description
            ))

            if application_id:
                conn.execute("""
                UPDATE applications
                SET status = 'DISPUTED', updated_at = CURRENT_TIMESTAMP
                WHERE application_id = ?
                """, (application_id,))

                conn.execute("""
                INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    application_id,
                    applicant_name,
                    "APPLICANT",
                    "COMPLAINT_FILED",
                    json.dumps({"case_id": case_id, "category": category, "priority": priority})
                ))
        return case_id
    finally:
        conn.close()


def list_complaint_cases() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM complaints_disputes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_complaint_case(case_id: str, status: str, resolution_summary: str, reviewer: str) -> bool:
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
            UPDATE complaints_disputes
            SET status = ?, resolution_summary = ?, assigned_reviewer = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE case_id = ?
            """, (status, resolution_summary, reviewer, case_id))
        return True
    finally:
        conn.close()


# Ensure database initializes when module is imported
init_db()
