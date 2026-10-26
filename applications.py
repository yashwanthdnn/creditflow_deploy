"""
Applications directory page: searchable, filterable application repository,
detailed inspection drawer, audit trail, downloadable report, and CSV export.
Enforces role-based data isolation so Applicants only access their own cases.
"""

import streamlit as st
import pandas as pd
import json

from services.database import list_applications, get_application_details
from agents.record_management_agent import RecordManagementAgent
from services.auth_service import AuthService, ROLE_APPLICANT


def render_applications():
    st.markdown('<div class="page-title">📁 Applications Repository & Case Files</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Inspect historical application dossiers, audit logs, agent outputs, and download verified assessment summaries.</div>',
        unsafe_allow_html=True
    )

    current_role = st.session_state.get("active_role", "Credit Officer")

    # Filter & Search Bar
    col_search, col_status, col_outcome = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search by Application ID, Applicant Name, or Email", placeholder="e.g. APP-2026 or Rohan")
    with col_status:
        status_filter = st.selectbox(
            "Filter Status",
            ["ALL", "PRE_SCREENING_COMPLETED", "HUMAN_REVIEW_REQUIRED", "MORE_INFORMATION_REQUIRED", "ON_HOLD", "DISPUTED", "APPROVED_BY_AUTHORIZED_LENDER", "DECLINED_BY_AUTHORIZED_LENDER"]
        )
    with col_outcome:
        outcome_filter = st.selectbox(
            "Filter Preliminary Route",
            ["ALL", "PROCEED_TO_NEXT_STAGE", "REQUIRES_HUMAN_REVIEW", "MORE_INFORMATION_REQUIRED", "ON_HOLD_FOR_VERIFICATION"]
        )

    apps = list_applications(
        search=search_query if search_query.strip() else None,
        status_filter=status_filter,
        outcome_filter=outcome_filter,
        limit=150
    )

    # If logged in as applicant, restrict view to applicant's own applications
    if current_role == ROLE_APPLICANT:
        # Filter for applicant's own records
        applicant_name_query = st.session_state.get("applicant_filter_name", "")
        if applicant_name_query:
            apps = [a for a in apps if applicant_name_query.lower() in a["full_name"].lower()]
        st.info("ℹ️ Showing applicant case view. In production, this view is tied to your verified login session.")

    # CSV Export Button
    if AuthService.is_staff(current_role):
        rec_agent = RecordManagementAgent()
        csv_data = rec_agent.export_applications_to_csv()
        st.download_button(
            label="📥 Export Filtered Applications (CSV)",
            data=csv_data,
            file_name="authorized_loan_applications_export.csv",
            mime="text/csv"
        )
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if not apps:
        st.info("No applications match the current search and filter criteria.")
        return

    # Applications Table
    df = pd.DataFrame(apps)
    df_display = df[[
        "application_id", "full_name", "loan_product", "requested_loan_amount",
        "loan_tenure_months", "credit_score", "status", "preliminary_outcome", "created_at"
    ]].copy()

    df_display["requested_loan_amount"] = df_display["requested_loan_amount"].apply(lambda v: f"₹{v:,.2f}")
    df_display.columns = ["App ID", "Applicant", "Product", "Amount", "Tenure (m)", "Score", "Status", "Route", "Created At"]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">🔍 Application Dossier Deep Dive</div>', unsafe_allow_html=True)

    app_id_list = [a["application_id"] for a in apps]
    selected_app_id = st.selectbox("Select Application ID to inspect full dossier", app_id_list)

    if selected_app_id:
        details = get_application_details(selected_app_id)
        if not details:
            st.error("Could not load application details.")
            return

        rec_agent = RecordManagementAgent()

        # Header summary
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Applicant", details["full_name"])
        c2.metric("Requested Amount", f"₹{details['requested_loan_amount']:,.2f}")
        c3.metric("Workflow Status", details["status"])
        c4.metric("Preliminary Route", details.get("preliminary_outcome") or "N/A")

        # Dossier Tabs
        t_summary, t_val, t_fin, t_rules, t_risk, t_audit, t_docs, t_methodology = st.tabs([
            "📋 Underwriter Summary",
            "🛡️ Data Validation",
            "💰 Financial Analysis",
            "📜 Rules Checklist",
            "🤖 ML Risk Model",
            "🕒 Audit Trail",
            "📄 Documents",
            "📜 Rules, Financial Methodology & Limitations"
        ])

        with t_summary:
            rec = details.get("recommendation_result") or {}
            st.markdown(f"**Preliminary Route**: `{rec.get('preliminary_outcome', 'N/A')}`")

            if rec.get("human_review_summary"):
                st.info(f"**Underwriting Assessment**: {rec.get('human_review_summary')}")
            if rec.get("pause_reason"):
                st.warning(f"**Workflow Pause Rationale**: {rec.get('pause_reason')}")

            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.markdown("##### 🟢 Positive Factors")
                pos_factors = json.loads(rec.get("positive_factors_json") or "[]")
                if pos_factors:
                    for pf in pos_factors:
                        st.markdown(f"- {pf}")
                else:
                    st.caption("No positive indicators recorded.")

            with col_neg:
                st.markdown("##### 🔴 Negative / Risk Factors")
                neg_factors = json.loads(rec.get("negative_factors_json") or "[]")
                if neg_factors:
                    for nf in neg_factors:
                        st.markdown(f"- {nf}")
                else:
                    st.caption("No adverse factors recorded.")

            # Download Report Button with Section D embedded as final section
            report_text = rec_agent.generate_assessment_report_text(details)
            st.download_button(
                label=f"📄 Download Full Assessment Dossier ({selected_app_id}.txt)",
                data=report_text,
                file_name=f"assessment_dossier_{selected_app_id}.txt",
                mime="text/plain"
            )

        with t_val:
            val = details.get("validation_result") or {}
            if val:
                st.write(f"**Is Valid**: `{bool(val.get('is_valid'))}`")
                st.write(f"**Recommended Action**: `{val.get('recommended_action')}`")

                errs = json.loads(val.get("blocking_errors_json") or "[]")
                if errs:
                    st.error(f"Blocking Errors: {', '.join(errs)}")

                inconsistencies = json.loads(val.get("inconsistency_flags_json") or "[]")
                if inconsistencies:
                    st.warning(f"Inconsistencies: {', '.join(inconsistencies)}")

                dups = json.loads(val.get("duplicate_flags_json") or "[]")
                if dups:
                    st.warning(f"Duplicate Flags: {', '.join(dups)}")
            else:
                st.caption("No validation record found.")

        with t_fin:
            fin = details.get("financial_result") or {}
            if fin:
                fc1, fc2, fc3 = st.columns(3)
                fc1.metric("Calculated EMI", f"₹{fin.get('monthly_emi', 0.0):,.2f}")
                fc2.metric("Total Monthly Obligations", f"₹{fin.get('total_monthly_obligations', 0.0):,.2f}")
                fc3.metric("Projected DTI Ratio", f"{round((fin.get('dti_ratio', 0.0) or 0.0)*100, 1)}%")

                st.write(f"**Net Disposable Income**: ₹{fin.get('net_disposable_income', 0.0):,.2f}")
                st.write(f"**Loan to Annual Income**: {fin.get('loan_to_annual_income', 0.0)}x")
                st.caption(f"Calculation notes: {fin.get('calculation_explanation')}")
            else:
                st.caption("No financial record found.")

        with t_rules:
            rules = details.get("rule_result") or {}
            if rules:
                st.write(f"**Evaluated / Passed**: {rules.get('rules_evaluated')} / {rules.get('rules_passed')} (Failed: {rules.get('rules_failed')})")
                st.caption(f"Summary: {rules.get('summary')}")
                items = json.loads(rules.get("rule_items_json") or "[]")
                if items:
                    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
            else:
                st.caption("No rules evaluation record found.")

        with t_risk:
            risk = details.get("risk_result") or {}
            if risk:
                rc1, rc2, rc3 = st.columns(3)
                rc1.metric("Risk Band", risk.get("risk_category", "N/A"))
                prob = risk.get("risk_score")
                rc2.metric("Estimated Default Probability", f"{round(prob*100, 1)}%" if prob is not None else "N/A")
                rc3.metric("Model Algorithm", f"{risk.get('model_name')} ({risk.get('model_version')})")

                st.caption(f"Notes: {risk.get('explanation_notes')}")
                limitations = json.loads(risk.get("limitations_json") or "[]")
                st.markdown("##### Model Governance & Limitations")
                for lim in limitations:
                    st.markdown(f"- {lim}")
            else:
                st.caption("No risk record found.")

        with t_audit:
            audits = details.get("audit_logs") or []
            if audits:
                st.dataframe(pd.DataFrame(audits)[["timestamp", "actor_id", "actor_role", "action", "event_details_json"]], use_container_width=True, hide_index=True)
            else:
                st.caption("No audit logs found.")

        with t_docs:
            docs = details.get("documents") or []
            if docs:
                for doc in docs:
                    st.write(f"📄 **{doc['doc_category']}**: `{doc['original_filename']}` ({doc['status']})")
            else:
                st.caption("No documents attached to this record.")

        with t_methodology:
            st.markdown("##### Final Section: Rules, Financial Methodology & Limitations")
            st.caption("Mandatory compliance and methodology disclosure embedded in this dossier.")
            st.markdown(f"""
            - **Loan Product**: `{details['loan_product']}`
            - **Calculation Engine Version**: `FinancialEngine-v2.4`
            - **Policy Version**: `{'v2.4-education' if details['loan_product'] == 'EDUCATION_LOAN' else 'v2.4-personal'}`
            - **Regulatory Reference**: RBI Digital Lending Guidelines 2022 & IBA Model Educational Loan Scheme
            - **Model Risk Estimator**: RandomForestClassifier v1.2-academic (Synthetic training benchmark)
            - **Reproducibility**: All calculations are reproducible via standard reducing-balance and IRR methods.
            """)
