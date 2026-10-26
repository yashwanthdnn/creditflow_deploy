"""
Fraud Investigation Desk: Case management for security alerts, duplicate detection,
tampered documents, and forensic investigation tracking.
"""

import streamlit as st
import json
import pandas as pd
from services.database import list_fraud_cases, resolve_fraud_case, get_application_details


def render_fraud_investigation():
    st.markdown('<div class="page-title">🛡️ Fraud & Security Investigation Desk</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Investigate suspicious application indicators, document inconsistencies, and identity duplicates in a secure sandbox.</div>',
        unsafe_allow_html=True
    )

    cases = list_fraud_cases()

    if not cases:
        st.success("🎉 **No Active Fraud Inquiries.** Zero suspicious activity flags currently registered in the security directory.")
        return

    st.markdown(f"**Security Incident Count**: `{len(cases)} registered fraud cases`")

    # Table of cases
    df_cases = pd.DataFrame(cases)
    display_cols = ["case_id", "application_id", "full_name", "loan_product", "status", "created_at"]
    st.dataframe(df_cases[display_cols], use_container_width=True, hide_index=True)

    st.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">🔍 Incident Investigation Dossier</div>', unsafe_allow_html=True)

    case_options = [c["case_id"] for c in cases]
    selected_case_id = st.selectbox("Select Case ID to Investigate", case_options)

    active_case = next(c for c in cases if c["case_id"] == selected_case_id)
    app_id = active_case["application_id"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Investigation Case ID", active_case["case_id"])
    col2.metric("Linked Application", app_id)
    col3.metric("Current Incident Status", active_case["status"])

    st.markdown("##### 🚨 Triggering Flags & Forensic Evidence")
    flags = json.loads(active_case.get("triggering_flags_json") or "[]")
    for flag in flags:
        st.error(f"- **Trigger**: {flag}")

    st.info(f"**Evidence Notes**: {active_case.get('evidence_notes') or 'N/A'}")

    # Resolution Form
    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
    st.markdown("##### ✍️ Update Investigation Findings & Incident Resolution")

    with st.form(f"resolve_fraud_form_{selected_case_id}"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            inv_id = st.text_input("Investigator Badge / ID *", value=st.session_state.get("user_id", "SEC-INV-07"))
            new_status = st.selectbox(
                "Investigation Resolution Status *",
                ["OPEN", "UNDER_INVESTIGATION", "CLEARED", "CONFIRMED_FRAUD"]
            )
        with f_col2:
            res_notes = st.text_area(
                "Investigator Resolution Findings *",
                value=active_case.get("resolution_notes") or "",
                placeholder="Detail verification calls, physical identity checks, or confirmation of synthetic test..."
            )

        submit = st.form_submit_button("Update Incident Record", type="primary")
        if submit:
            if not res_notes.strip():
                st.error("Resolution findings notes are required.")
            else:
                ok = resolve_fraud_case(
                    case_id=selected_case_id,
                    status=new_status,
                    resolution_notes=res_notes.strip(),
                    investigator_id=inv_id.strip()
                )
                if ok:
                    st.success(f"Case {selected_case_id} updated to {new_status}!")
                    st.rerun()
                else:
                    st.error("Failed to update fraud case.")
