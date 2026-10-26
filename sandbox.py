"""
Secure Assessment Sandbox Workspace (Section E).
Authenticated workbench for Credit Officers, Fraud Investigators, and Administrators.
Completely isolated execution and persistence in data/sandbox_evaluations.db.
Allows staff to stress-test policies, simulate system failures, inspect agent execution traces,
and test scenarios safely with zero risk to production intake.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List

from services.sandbox_service import SandboxService
from services.financial_engine import FinancialEngine
from services.auth_service import AuthService, ROLE_APPLICANT
from models.schemas import DocumentStatus


def render_sandbox():
    current_role = st.session_state.get("active_role", "Credit Officer")

    # Strict server-side RBAC enforcement
    if not AuthService.is_staff(current_role):
        st.error("🚫 Access Denied: The Secure Assessment Sandbox is strictly restricted to authorized staff (Credit Officers, Fraud Investigators, and Administrators).")
        st.info("Applicants do not have access to internal simulation environments.")
        return

    # Log staff entry into sandbox
    AuthService.log_staff_access(
        actor_id=f"STAFF-{current_role.upper()}",
        actor_role=current_role,
        resource_type="sandbox_workspace",
        resource_id="ENVIRONMENT_ACCESS",
        action="ENTER_SECURE_SANDBOX"
    )

    # Mandatory Sandbox Banner (Section E)
    st.markdown("""
    <div style="background-color: #FEF3C7; border-left: 6px solid #D97706; padding: 14px 18px; border-radius: 8px; margin-bottom: 20px;">
        <span style="font-weight: 800; color: #92400E; font-size: 0.95rem;">
            🛡️ SECURE TEST ENVIRONMENT — Use synthetic data only. Results are for testing and preliminary assessment. This environment does not sanction or disburse loans.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-title">🧪 Secure Assessment Sandbox & Stress-Test Studio</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Isolated test laboratory. All runs, agent logs, and test data are stored in <code>data/sandbox_evaluations.db</code> without touching production intake.</div>',
        unsafe_allow_html=True
    )

    presets = SandboxService.get_synthetic_presets()

    # Top Controls: Preset selector and new scenario generator
    sb_tab1, sb_tab2, sb_tab3 = st.tabs([
        "🔬 Scenario Configuration & Simulation",
        "📑 Evaluation History & Trace Inspector",
        "⚙️ Database & Policy Isolation Controls"
    ])

    with sb_tab1:
        st.markdown("#### 1. Select or Customize Synthetic Test Scenario")
        preset_key = st.selectbox(
            "Choose a Pre-Configured Synthetic Benchmark Scenario",
            list(presets.keys()),
            format_func=lambda k: presets[k]["name"]
        )
        selected_preset = presets[preset_key]

        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            scenario_name = st.text_input("Scenario Name", value=selected_preset["name"])
            loan_product = st.selectbox(
                "Loan Product Category",
                ["PERSONAL_LOAN", "EDUCATION_LOAN"],
                index=0 if selected_preset["product"] == "PERSONAL_LOAN" else 1
            )
        with col_s2:
            st.info(f"Targeting: **{loan_product}** | Isolation Level: **SQLite Isolated Sandbox DB**")

        st.markdown("#### 2. Edit Synthetic Applicant & Financial Parameters")
        p_app = selected_preset["applicant"]

        if loan_product == "PERSONAL_LOAN":
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                s_name = st.text_input("Synthetic Name", value=p_app.get("full_name", "Synthetic Applicant"))
                s_age = st.number_input("Age", min_value=18, max_value=85, value=p_app.get("age", 32))
                s_income = st.number_input("Monthly Take-Home Income (₹)", min_value=5000.0, max_value=2000000.0, value=float(p_app.get("monthly_take_home", 75000.0)), step=5000.0)
                s_existing_emi = st.number_input("Existing Monthly Debt Obligations (₹)", min_value=0.0, max_value=1000000.0, value=float(p_app.get("existing_monthly_obligations", 10000.0)), step=2500.0)
            with f_col2:
                s_amount = st.number_input("Requested Principal Loan Amount (₹)", min_value=25000.0, max_value=5000000.0, value=float(p_app.get("requested_loan_amount", 400000.0)), step=25000.0)
                s_tenure = st.number_input("Loan Tenure (Months)", min_value=6, max_value=84, value=int(p_app.get("loan_tenure_months", 36)), step=6)
                s_rate = st.number_input("Nominal Annual Interest Rate (%)", min_value=8.0, max_value=28.0, value=float(p_app.get("proposed_interest_rate", 11.5)), step=0.25)
                s_score = st.number_input("Simulated Bureau Score", min_value=300, max_value=850, value=int(p_app.get("credit_score") or 720))

            synthetic_applicant_data = {
                "full_name": s_name,
                "loan_product": "PERSONAL_LOAN",
                "age": int(s_age),
                "monthly_income": float(s_income),
                "existing_monthly_obligations": float(s_existing_emi),
                "requested_loan_amount": float(s_amount),
                "loan_tenure_months": int(s_tenure),
                "proposed_interest_rate": float(s_rate),
                "credit_score": int(s_score),
                "credit_score_source": "Authorized Bureau Synthetic Simulator",
                "consent_given": True
            }

        else: # EDUCATION_LOAN
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                e_name = st.text_input("Synthetic Student Name", value=p_app.get("full_name", "Synthetic Student"))
                e_univ = st.text_input("University / College", value=p_app.get("university_name", "Premier State Tech University"))
                e_pin = st.text_input("College PIN Code", value=p_app.get("college_pin_code", "560012"))
                e_state = st.text_input("City / District / State", value=p_app.get("city_district_state", "Bengaluru, Karnataka"))
                e_adm_status = st.selectbox(
                    "Admission Offer Status",
                    ["Confirmed Admission", "Provisional Offer Received", "Applied"],
                    index=0 if p_app.get("admission_status") == "Confirmed Admission" else (1 if p_app.get("admission_status") == "Provisional Offer Received" else 2)
                )
                e_letter_no = st.text_input("Offer Letter Ref Number", value=p_app.get("admission_letter_number", "OFFER-2026-99"))
            with e_col2:
                e_amount = st.number_input("Requested Education Loan Amount (₹)", min_value=50000.0, max_value=15000000.0, value=float(p_app.get("requested_loan_amount", 800000.0)), step=50000.0)
                e_tenure = st.number_input("Repayment Tenure (Months)", min_value=12, max_value=180, value=int(p_app.get("loan_tenure_months", 84)), step=12)
                e_morat = st.number_input("Moratorium Months", min_value=6, max_value=84, value=int(p_app.get("moratorium_months", 36)), step=6)
                e_rate = st.number_input("Interest Rate (%)", min_value=6.0, max_value=18.0, value=float(p_app.get("proposed_interest_rate", 9.25)), step=0.25)
                e_coapp_name = st.text_input("Co-Applicant Name", value=p_app.get("co_applicant_name", "Parent Co-Applicant"))
                e_coapp_income = st.number_input("Co-Applicant Monthly Income (₹)", min_value=0.0, max_value=2000000.0, value=float(p_app.get("co_applicant_income", 90000.0)), step=5000.0)
                e_coapp_emi = st.number_input("Co-Applicant Existing EMIs (₹)", min_value=0.0, max_value=1000000.0, value=float(p_app.get("co_applicant_existing_emi", 12000.0)), step=2500.0)

            synthetic_applicant_data = {
                "full_name": e_name,
                "loan_product": "EDUCATION_LOAN",
                "university_name": e_univ,
                "college_institution_name": e_univ,
                "college_pin_code": e_pin,
                "city_district_state": e_state,
                "country_of_study": "India",
                "admission_status": e_adm_status,
                "admission_letter_number": e_letter_no,
                "requested_loan_amount": float(e_amount),
                "loan_tenure_months": int(e_tenure),
                "moratorium_months": int(e_morat),
                "proposed_interest_rate": float(e_rate),
                "monthly_income": 0.0,
                "co_applicant_name": e_coapp_name,
                "co_applicant_income": float(e_coapp_income),
                "co_applicant_existing_emi": float(e_coapp_emi),
                "tuition_fees": float(e_amount * 0.7),
                "hostel_living_cost": float(e_amount * 0.3),
                "confirmed_scholarship": 0.0,
                "unconfirmed_scholarship": 0.0,
                "student_contribution": 0.0,
                "credit_score": 750,
                "consent_given": True
            }

        st.markdown("#### 3. Select Document Verification Lifecycle States (12 States)")
        st.caption("Test how the workflow reacts when documents are in various verification stages.")

        configured_docs = list(selected_preset["documents"])
        status_options = [s.value for s in DocumentStatus]

        simulated_docs = []
        for d in configured_docs:
            req_id = d["requirement_id"]
            curr_stat = d["status"]
            sel_idx = status_options.index(curr_stat) if curr_stat in status_options else 1
            col_doc1, col_doc2 = st.columns([1, 2])
            with col_doc1:
                st.write(f"**{req_id}**")
            with col_doc2:
                chosen_status = st.selectbox(
                    f"State for {req_id}",
                    status_options,
                    index=sel_idx,
                    key=f"sbx_doc_stat_{req_id}",
                    label_visibility="collapsed"
                )
                simulated_docs.append({"requirement_id": req_id, "status": chosen_status})

        st.markdown("#### 4. Simulation Toggles & Fault Injection")
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            sim_fail_integ = st.checkbox("Simulate Bureau / KYC API Outage (503 Gateway)", value=False)
        with sim_col2:
            sim_unavail_ml = st.checkbox("Simulate ML Model Unavailable (Offline)", value=False)
        with sim_col3:
            sim_tamper = st.checkbox("Simulate Inconsistent Form Inputs", value=False)

        if sim_tamper:
            synthetic_applicant_data["college_pin_code"] = "999999"  # invalid PIN
            synthetic_applicant_data["existing_monthly_obligations"] = 999999.0

        simulation_flags = {
            "simulate_failed_integration": sim_fail_integ,
            "simulate_unavailable_model": sim_unavail_ml,
            "simulate_tampered_docs": sim_tamper
        }

        st.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
        if st.button("🚀 Execute Isolated Seven-Agent Sandbox Workflow", type="primary"):
            with st.spinner("Executing isolated pipeline in sandbox database..."):
                res = SandboxService.execute_sandbox_workflow(
                    scenario_name=scenario_name,
                    applicant_data=synthetic_applicant_data,
                    documents=simulated_docs,
                    simulation_flags=simulation_flags,
                    staff_role=current_role
                )

            st.session_state["latest_sandbox_result"] = res
            st.success(f"Sandbox Run Completed! ID: `{res['sandbox_id']}`")

        # Display result if available
        if "latest_sandbox_result" in st.session_state:
            res = st.session_state["latest_sandbox_result"]
            st.markdown("---")
            st.markdown(f"### Sandbox Evaluation Summary: `{res['sandbox_id']}`")

            # Outcome card
            outcome = res["preliminary_outcome"]
            if outcome == "PROCEED_TO_NEXT_STAGE":
                st.success(f"🎉 **Outcome: {outcome}** — {res['outcome_reason']}")
            elif outcome == "MORE_INFORMATION_REQUIRED":
                st.warning(f"⚠️ **Outcome: {outcome}** — {res['outcome_reason']}")
            elif outcome == "REQUIRES_HUMAN_REVIEW":
                st.error(f"🛑 **Outcome: {outcome}** — {res['outcome_reason']}")
            else:
                st.info(f"⏳ **Outcome: {outcome}** — {res['outcome_reason']}")

            # Agent traces
            st.markdown("##### Agent Execution Trace Waterfall (Sandbox Database)")
            for trace in res["agent_traces"]:
                status_color = "🟢" if trace["status"] == "SUCCESS" else ("🟡" if trace["status"] == "WARNING" else "🔴")
                with st.expander(f"{status_color} **{trace['agent_name']}** — {trace['status']} ({trace['duration_ms']} ms)"):
                    st.write(f"• **Inputs**: `{trace['input_summary']}`")
                    st.write(f"• **Outputs**: `{trace['output_summary']}`")
                    if trace.get("escalation_reason"):
                        st.warning(f"• **Escalation Reason**: {trace['escalation_reason']}")

            # Financial results card
            st.markdown("##### Calculated Financial Results & What-If Sandbox")
            fin = res["financials"]
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                st.metric("Monthly EMI", f"₹{fin['monthly_emi']:,.2f}")
            with fc2:
                st.metric("Net Disbursed", f"₹{fin['net_disbursed']:,.2f}")
            with fc3:
                st.metric("APR (IRR)", f"{fin['apr_pct']}%" if fin['apr_pct'] else "N/A")
            with fc4:
                st.metric("Upfront Deductions", f"₹{fin['total_upfront_deductions']:,.2f}")

            # Education moratorium card
            if fin.get("edu_moratorium"):
                morat = fin["edu_moratorium"]
                st.info(
                    f"**Education Moratorium Breakdown**:\n\n"
                    f"• Study-Period Interest: ₹{morat['study_period_interest']:,.2f}\n"
                    f"• Capitalized Balance at Repayment: ₹{morat['capitalized_principal']:,.2f}\n"
                    f"• Post-Moratorium Monthly EMI: ₹{morat['post_moratorium_monthly_emi']:,.2f}"
                )

            # JSON download of synthetic dossier
            st.download_button(
                "📥 Download Synthetic Assessment Dossier (JSON)",
                data=json.dumps(res, indent=2),
                file_name=f"{res['sandbox_id']}_dossier.json",
                mime="application/json"
            )

    with sb_tab2:
        st.markdown("#### Sandbox Evaluation Run History")
        st.caption("Persisted runs in `data/sandbox_evaluations.db` (Independent of production intake).")

        evals = SandboxService.list_sandbox_evaluations()
        if not evals:
            st.info("No sandbox evaluation runs found yet. Execute a simulation above to generate records.")
        else:
            for ev in evals:
                with st.expander(f"🔬 {ev['sandbox_id']}: {ev['scenario_name']} [{ev['loan_product']}] — {ev['preliminary_outcome']}"):
                    st.write(f"• **Executed By**: {ev['created_by_role']} | **Timestamp**: {ev['created_at']}")
                    st.write(f"• **Workflow Status**: {ev['status']} | **Preliminary Route**: {ev['preliminary_outcome']}")
                    if st.button("Inspect Detailed Agent Trace", key=f"insp_{ev['sandbox_id']}"):
                        full_ev = SandboxService.get_sandbox_evaluation(ev['sandbox_id'])
                        if full_ev:
                            st.json(full_ev.get("agent_runs", []))

    with sb_tab3:
        st.markdown("#### Database Isolation & Reset Controls")
        st.warning("All operations in this tab operate EXCLUSIVELY on `data/sandbox_evaluations.db`. The production database `credit_assessment.db` is strictly untouched.")

        st.write("• **Sandbox Database Path**: `data/sandbox_evaluations.db`")
        st.write("• **Production Database Path**: `data/credit_assessment.db`")
        st.write("• **Cross-Contamination Protection**: Enforced via separate SQLite connection handles and schema isolation.")

        if st.button("🗑️ Reset All Sandbox Scenarios & Purge Sandbox DB", type="secondary"):
            purged_count = SandboxService.reset_sandbox_database()
            st.success(f"Successfully purged all synthetic sandbox records! Production application records remain 100% intact.")
            st.rerun()
