"""
Human Review Queue: Dedicated underwriting workbench for authorized credit officers
to investigate policy exceptions, review evidence, and record binding decisions separately from AI.
"""

import streamlit as st
import json
from services.database import list_applications, get_application_details, record_human_review


def render_human_review_queue():
    st.markdown('<div class="page-title">👤 Underwriter & Credit Officer Human Review Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Authorized credit committee workbench for evaluating escalated cases, policy overrides, and exceptional risk circumstances.</div>',
        unsafe_allow_html=True
    )

    # Filter to cases requiring human review
    apps_review = list_applications(status_filter="HUMAN_REVIEW_REQUIRED", limit=100)
    apps_hold = list_applications(status_filter="ON_HOLD", limit=100)
    combined_cases = apps_review + [a for a in apps_hold if a not in apps_review]

    if not combined_cases:
        st.success("🎉 **No Pending Cases in Review Queue!** All active applications have either progressed automatically or been finalized.")
        return

    st.markdown(f"**Pending Queue Count**: `{len(combined_cases)} case(s) requiring underwriter intervention`")

    case_options = [f"{c['application_id']} — {c['full_name']} (₹{c['requested_loan_amount']:,.2f}, {c['loan_product']})" for c in combined_cases]
    selected_idx = st.selectbox("Select Case File from Queue", range(len(case_options)), format_func=lambda i: case_options[i])

    active_app_id = combined_cases[selected_idx]["application_id"]
    details = get_application_details(active_app_id)

    if not details:
        st.error("Case details not accessible.")
        return

    # Case Dossier Overview
    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Applicant", details["full_name"])
    col2.metric("Requested Principal", f"₹{details['requested_loan_amount']:,.2f}")
    col3.metric("Declared Income", f"₹{details['monthly_income']:,.2f}/mo")
    col4.metric("Current State", details["status"])

    # Escalation Breakdown
    rec = details.get("recommendation_result") or {}
    val = details.get("validation_result") or {}
    fin = details.get("financial_result") or {}
    rules = details.get("rule_result") or {}
    risk = details.get("risk_result") or {}

    st.markdown("##### 🚨 Escalation Rationale & AI Advisory Findings")
    if rec.get("human_review_summary"):
        st.error(f"**Underwriting Escalation**: {rec.get('human_review_summary')}")
    if rec.get("pause_reason"):
        st.warning(f"**Pause Trigger**: {rec.get('pause_reason')}")

    # Evidence details
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        st.markdown("###### Financial Debt Ratios")
        st.write(f"- Calculated EMI: **₹{fin.get('monthly_emi', 0.0):,.2f}**")
        st.write(f"- Total Obligations: **₹{fin.get('total_monthly_obligations', 0.0):,.2f}**")
        st.write(f"- Projected DTI: **{round((fin.get('dti_ratio', 0.0) or 0.0)*100, 1)}%**")
        st.write(f"- Net Disposable Cushion: **₹{fin.get('net_disposable_income', 0.0):,.2f}**")

    with e_col2:
        st.markdown("###### Rules & Model Signals")
        st.write(f"- Policy Rules Failed: **{rules.get('rules_failed', 0)}** of {rules.get('rules_evaluated', 0)}")
        prob = risk.get("risk_score")
        st.write(f"- ML Default Probability: **{round(prob*100, 1)}%** ({risk.get('risk_category', 'N/A')})" if prob is not None else "- ML Prediction: N/A")
        st.write(f"- Credit Bureau Score: **{details.get('credit_score') or 'Unscored'}**")

    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">✍️ Authorized Credit Officer Decision Recording</div>', unsafe_allow_html=True)
    st.caption("Human oversight mandate: The decision below represents an independent, authorized human underwriter determination.")

    with st.form(f"human_review_form_{active_app_id}"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            reviewer_name = st.text_input("Reviewer Officer Official Name *", value=st.session_state.get("user_name", "Jane Doe, Senior Credit Officer"))
            reviewer_id = st.text_input("Officer Employee ID *", value=st.session_state.get("user_id", "OFFICER-101"))
            reviewer_role = st.selectbox("Authorization Authority Role *", ["Credit Officer", "Chief Underwriter", "Sanction Committee Member"])

        with f_col2:
            decision = st.selectbox(
                "Formal Underwriting Determination *",
                [
                    ("APPROVE", "Approve Loan (Override exceptions with justification)"),
                    ("DECLINE", "Decline Loan (Unacceptable credit/policy risk)"),
                    ("REQUEST_INFO", "Request More Information (Return to applicant)"),
                    ("MAINTAIN_REVIEW", "Keep Under Review (Pending field verification)")
                ],
                format_func=lambda x: x[1]
            )

        findings = st.text_area(
            "Underwriter Findings & Risk Justification *",
            placeholder="Record the official clinical rationale, policy exception notes, or documentary justifications...",
            help="Mandatory audit trail requirement. Clearly specify reasons if overriding AI warnings."
        )

        conditions = st.text_input(
            "Sanction Conditions / Stipulations (Optional)",
            placeholder="e.g. Co-applicant guarantee required prior to disbursement."
        )

        submitted = st.form_submit_button("🔒 Record & Commit Authorized Human Decision", type="primary")

        if submitted:
            if not findings.strip():
                st.error("Underwriter findings & justification are mandatory.")
            else:
                ok = record_human_review(
                    application_id=active_app_id,
                    reviewer_id=reviewer_id.strip(),
                    reviewer_name=reviewer_name.strip(),
                    role=reviewer_role,
                    decision=decision[0],
                    findings=findings.strip(),
                    conditions=conditions.strip()
                )
                if ok:
                    st.success(f"✅ Human decision '{decision[0]}' committed for Application {active_app_id}! Updated audit logs.")
                    st.rerun()
                else:
                    st.error("Failed to commit review to database.")
