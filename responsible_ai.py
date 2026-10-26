"""
Responsible AI, System Governance, and Configuration Settings Page.
Features ethical AI disclaimers, data minimization controls, integration toggles,
configurable thresholds, and synthetic demonstration scenario injection.
"""

import streamlit as st
import uuid
from config.settings import (
    ACADEMIC_PROTOTYPE_DISCLAIMER,
    DEFAULT_ANNUAL_INTEREST_RATE,
    MAX_PERMITTED_DTI,
    MIN_MONTHLY_INCOME,
    MIN_APPLICANT_AGE,
    MAX_APPLICANT_AGE
)
from agents.coordinator_agent import CoordinatorAgent
from ml.train_model import train_and_compare_models


def render_responsible_ai():
    st.markdown('<div class="page-title">⚙️ Responsible AI, Governance & Settings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Algorithmic fairness documentation, privacy controls, integration sandboxes, and academic demonstration tools.</div>',
        unsafe_allow_html=True
    )

    tab_gov, tab_config, tab_test = st.tabs([
        "🛡️ Responsible AI & Ethical Framework",
        "⚙️ Lending Policy & Integration Toggles",
        "🧪 Synthetic Test Scenario Injector"
    ])

    with tab_gov:
        st.markdown('<div class="section-card-title">Institutional Academic Prototype Disclaimer</div>', unsafe_allow_html=True)
        st.warning(f"**Mandatory Regulatory Notice**: {ACADEMIC_PROTOTYPE_DISCLAIMER}")

        st.markdown("##### Core Responsible AI Principles Implemented")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - **Non-Exclusivity of AI Decisions**: The AI system acts strictly in a pre-screening and decision-support capacity. Final legal approvals or denials are reserved for authorized human credit officers.
            - **No Automatic Rejections**: High default risk scores or policy warnings escalate the case to the Human Review Queue rather than triggering silent rejections.
            - **Explainability & Traceability**: Every assessment provides positive and negative factors directly tied to mathematical ratios, configurable rules, and verified documents.
            """)

        with col2:
            st.markdown("""
            - **Data Minimization**: Prohibits storage of raw government ID cards, biometric faces, OTPs, PINs, or full payment credentials.
            - **Fair Lending & Anti-Bias**: Protected demographic attributes (gender, religion, caste, marital status) are excluded from feature engineering and credit risk models.
            - **Immutable Audit Trail**: All state transitions, reviewer overrides, and agent runtimes are logged with timestamps in SQLite.
            """)

    with tab_config:
        st.markdown('<div class="section-card-title">Configurable Product Parameters</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Baseline Annual Interest Rate (%)", value=DEFAULT_ANNUAL_INTEREST_RATE, disabled=True)
            st.number_input("Max Permitted Debt-to-Income (DTI)", value=MAX_PERMITTED_DTI, disabled=True)
            st.number_input("Minimum Monthly Income Baseline (₹)", value=MIN_MONTHLY_INCOME, disabled=True)
        with c2:
            st.number_input("Minimum Permissible Age", value=MIN_APPLICANT_AGE, disabled=True)
            st.number_input("Maximum Working Age at Maturity", value=MAX_APPLICANT_AGE, disabled=True)

        st.markdown("##### External Integration Sandboxes")
        st.write("Current Environment Modes:")
        st.success("🟢 Simulated KYC Provider: `SIMULATED_MOCK` (Synthetic tokens)")
        st.success("🟢 Simulated Credit Bureau: `SIMULATED_MOCK` (Sandbox reports)")
        st.success("🟢 Simulated Account Aggregator: `SIMULATED_MOCK` (Synthetic cashflow)")
        st.warning("⚠️ Real Loan Disbursements: `STRICTLY_DISABLED` (Academic safety lock)")

        st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
        if st.button("🔄 Retrain Credit Risk ML Models On-Demand"):
            with st.spinner("Retraining Logistic Regression, Decision Tree, and Random Forest pipelines..."):
                meta = train_and_compare_models()
            st.success(f"Retrained successfully! Champion model: {meta['selected_model']}")

    with tab_test:
        st.markdown('<div class="section-card-title">🧪 Synthetic Demonstration Scenarios</div>', unsafe_allow_html=True)
        st.caption("Inject pre-configured synthetic academic profiles to demonstrate specific edge cases, escalations, or straightforward passes.")

        scenarios = {
            "Scenario A: Prime Salaried Applicant (Auto-Progression)": {
                "full_name": "Rohan Sharma",
                "email": "rohan.sharma@example.edu",
                "phone": "+91-9876543210",
                "date_of_birth": "1994-05-12",
                "age": 31,
                "employment_type": "Salaried Full-Time",
                "employment_months": 48,
                "monthly_income": 95000.0,
                "existing_monthly_obligations": 5000.0,
                "dependents": 1,
                "loan_product": "PERSONAL_LOAN",
                "requested_loan_amount": 250000.0,
                "loan_tenure_months": 36,
                "proposed_interest_rate": 10.5,
                "credit_score": 780,
                "previous_defaults_count": 0,
                "consent_given": True,
                "national_id_number": f"PAN{uuid.uuid4().hex[:6].upper()}",
                "docs": [
                    {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
                    {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
                    {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
                    {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
                ]
            },
            "Scenario B: High Debt Burden (DTI > 65% Escalation)": {
                "full_name": "Suresh Raina",
                "email": "suresh.raina@example.edu",
                "phone": "+91-9876543211",
                "date_of_birth": "1988-10-20",
                "age": 37,
                "employment_type": "Self-Employed Business",
                "employment_months": 18,
                "monthly_income": 40000.0,
                "existing_monthly_obligations": 22000.0,  # 55% DTI already
                "dependents": 2,
                "loan_product": "PERSONAL_LOAN",
                "requested_loan_amount": 350000.0,  # Pushes DTI over 75%
                "loan_tenure_months": 24,
                "proposed_interest_rate": 13.5,
                "credit_score": 620,
                "previous_defaults_count": 1,
                "consent_given": True,
                "national_id_number": f"PAN{uuid.uuid4().hex[:6].upper()}",
                "docs": [
                    {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
                    {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
                    {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
                    {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
                ]
            },
            "Scenario C: Underage Applicant (Blocking Policy Exception)": {
                "full_name": "Aarav Patel (Student)",
                "email": "aarav.p@campus.edu",
                "phone": "+91-9876543212",
                "date_of_birth": "2010-08-14",
                "age": 15,  # Under 18
                "employment_type": "Student",
                "employment_months": 0,
                "monthly_income": 20000.0,
                "existing_monthly_obligations": 0.0,
                "dependents": 0,
                "loan_product": "PERSONAL_LOAN",
                "requested_loan_amount": 50000.0,
                "loan_tenure_months": 12,
                "proposed_interest_rate": 12.0,
                "credit_score": 650,
                "previous_defaults_count": 0,
                "consent_given": True,
                "national_id_number": f"PAN{uuid.uuid4().hex[:6].upper()}",
                "docs": [
                    {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
                    {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
                    {"doc_category": "PHOTOGRAPH", "status": "Uploaded"},
                    {"doc_category": "INCOME_PROOF", "status": "Uploaded"}
                ]
            },
            "Scenario D: Identity & Document Income Mismatch (Fraud Trigger)": {
                "full_name": "Vikram Seth",
                "email": "vikram.seth@example.org",
                "phone": "+91-9876543213",
                "date_of_birth": "1991-03-25",
                "age": 34,
                "employment_type": "Salaried Full-Time",
                "employment_months": 24,
                "monthly_income": 120000.0,  # Claimed 120k
                "existing_monthly_obligations": 10000.0,
                "dependents": 1,
                "loan_product": "PERSONAL_LOAN",
                "requested_loan_amount": 500000.0,
                "loan_tenure_months": 36,
                "proposed_interest_rate": 11.0,
                "credit_score": 720,
                "previous_defaults_count": 0,
                "consent_given": True,
                "national_id_number": f"PAN{uuid.uuid4().hex[:6].upper()}",
                "docs": [
                    {
                        "doc_category": "INCOME_PROOF",
                        "status": "Uploaded",
                        "original_filename": "salary_slip_modified.pdf",
                        "extracted_fields": {"detected_monthly_income": 25000.0}  # Extraction only 25k!
                    },
                    {"doc_category": "IDENTITY_PROOF", "status": "Uploaded"},
                    {"doc_category": "ADDRESS_PROOF", "status": "Uploaded"},
                    {"doc_category": "PHOTOGRAPH", "status": "Uploaded"}
                ]
            }
        }

        selected_scenario_name = st.selectbox("Choose Synthetic Academic Scenario", list(scenarios.keys()))
        scenario_data = scenarios[selected_scenario_name]

        if st.button("🚀 Inject & Execute Synthetic Scenario Assessment", type="primary"):
            coordinator = CoordinatorAgent()
            docs = scenario_data.pop("docs", [])
            with st.spinner("Processing scenario through Coordinator Agent..."):
                res = coordinator.process_application(scenario_data, uploaded_documents=docs)

            app_id = res["application_id"]
            status = res["status"]
            outcome = res["preliminary_outcome"]

            st.success(f"Execution Completed! Application `{app_id}` -> Status: `{status}`, Outcome: `{outcome}`")
            st.info("You can now view this case in **Dashboard**, **Applications**, **Human Review Queue**, or **Agent Execution Logs**.")
