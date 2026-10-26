"""
Complaints & Disputes Desk: Dedicated dispute resolution workflow for applicant grievances,
contested credit reports, alleged identity theft, or application inaccuracies.
"""

import streamlit as st
import pandas as pd
from services.database import list_complaint_cases, create_complaint_case, resolve_complaint_case, list_applications


def render_complaints_disputes():
    st.markdown('<div class="page-title">⚖️ Applicant Complaints & Disputes Desk</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Fair lending grievance tracking: investigate contested credit-bureau items, disputed income figures, or identity disputes.</div>',
        unsafe_allow_html=True
    )

    tab_list, tab_new = st.tabs(["Active Grievance Tickets", "➕ Register New Dispute"])

    with tab_list:
        cases = list_complaint_cases()
        if not cases:
            st.info("No complaints or disputes currently open in the register.")
        else:
            df = pd.DataFrame(cases)
            st.dataframe(df[["case_id", "application_id", "applicant_name", "category", "priority", "status", "created_at"]], use_container_width=True, hide_index=True)

            st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
            st.markdown("##### ✍️ Adjudicate & Resolve Dispute Ticket")

            case_ids = [c["case_id"] for c in cases]
            selected_id = st.selectbox("Select Dispute Ticket ID", case_ids)
            target_case = next(c for c in cases if c["case_id"] == selected_id)

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Applicant**: `{target_case['applicant_name']}` ({target_case['contact_info']})")
                st.write(f"**Linked Application**: `{target_case.get('application_id') or 'N/A'}`")
                st.write(f"**Dispute Category**: `{target_case['category']}`")
                st.write(f"**Priority Tier**: `{target_case['priority']}`")
            with col2:
                st.info(f"**Applicant Statement**: {target_case['description']}")

            with st.form(f"resolve_dispute_{selected_id}"):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    reviewer = st.text_input("Grievance Officer Name *", value=st.session_state.get("user_name", "Compliance Officer Anita"))
                    new_status = st.selectbox("Resolution State", ["ASSIGNED", "UNDER_REVIEW", "RESOLVED", "CLOSED"])
                with r_col2:
                    summary = st.text_area(
                        "Adjudication Summary & Action *",
                        value=target_case.get("resolution_summary") or "",
                        placeholder="Detail bureau re-inquiry, correction of income baseline, or applicant response..."
                    )

                if st.form_submit_button("Commit Dispute Determination", type="primary"):
                    if not summary.strip():
                        st.error("Adjudication summary is mandatory.")
                    else:
                        ok = resolve_complaint_case(
                            case_id=selected_id,
                            status=new_status,
                            resolution_summary=summary.strip(),
                            reviewer=reviewer.strip()
                        )
                        if ok:
                            st.success(f"Ticket {selected_id} updated to {new_status}!")
                            st.rerun()

    with tab_new:
        st.markdown("##### Register a Formal Dispute / Grievance")
        apps = list_applications(limit=50)
        app_opts = ["None / General Dispute"] + [a["application_id"] for a in apps]

        with st.form("new_dispute_form"):
            c1, c2 = st.columns(2)
            with c1:
                app_ref = st.selectbox("Application Reference (Optional)", app_opts)
                app_name = st.text_input("Applicant Official Name *", placeholder="e.g. Mohit Sharma")
                contact = st.text_input("Contact Email / Phone *", placeholder="e.g. mohit@example.in")

            with c2:
                category = st.selectbox(
                    "Grievance Category *",
                    ["DISPUTED_CREDIT_INFO", "IDENTITY_THEFT", "INCORRECT_DATA", "DISPUTED_EXPLANATION", "OTHER"]
                )
                priority = st.selectbox("Urgency Priority *", ["LOW", "MEDIUM", "HIGH", "URGENT"])

            desc = st.text_area(
                "Detailed Description of Disputed Item *",
                placeholder="Explain the specific factual inaccuracy, contested bureau account, or documentation discrepancy..."
            )

            if st.form_submit_button("Submit Dispute Ticket", type="primary"):
                if not app_name.strip() or not desc.strip():
                    st.error("Applicant name and description are required.")
                else:
                    ref_id = None if app_ref.startswith("None") else app_ref
                    new_cid = create_complaint_case(
                        application_id=ref_id,
                        applicant_name=app_name.strip(),
                        contact_info=contact.strip(),
                        category=category,
                        priority=priority,
                        description=desc.strip()
                    )
                    st.success(f"Dispute ticket `{new_cid}` created! Placed associated application on hold.")
                    st.rerun()
