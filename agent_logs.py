"""
Agent Execution Logs: Detailed visual trace and telemetry for all seven agents across workflow runs.
"""

import streamlit as st
import pandas as pd
from services.database import list_applications, get_application_details


def render_agent_logs():
    st.markdown('<div class="page-title">🔄 Agent Execution Logs & Workflow Telemetry</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Inspect runtime execution sequence, duration (ms), inputs/outputs, and decision triggers across all seven agents.</div>',
        unsafe_allow_html=True
    )

    apps = list_applications(limit=60)
    if not apps:
        st.info("No applications in database to inspect logs for.")
        return

    app_id_list = [a["application_id"] for a in apps]
    selected_app_id = st.selectbox("Select Application to Inspect Agent Trace", app_id_list)

    details = get_application_details(selected_app_id)
    if not details:
        st.error("Could not load details.")
        return

    runs = details.get("agent_runs", [])
    st.markdown(f"**Application**: `{selected_app_id}` | **Status**: `{details['status']}` | **Logged Agent Runs**: `{len(runs)}`")

    st.markdown("#### Canonical Agent Architecture Sequence")
    st.markdown("""
    ```text
    1. Coordinator Agent (agents/coordinator_agent.py)
       ↳ 2. Data Validation Agent (agents/data_validation_agent.py)
          ↳ 3. Financial Analysis Agent (agents/financial_analysis_agent.py)
             ↳ 4. Eligibility and Rules Agent (agents/eligibility_rules_agent.py)
                ↳ 5. Credit Risk Agent (agents/credit_risk_agent.py)
                   ↳ 6. Risk Explanation & Recommendation Agent (agents/risk_explanation_agent.py)
                      ↳ 7. Final Record Management Agent (agents/record_management_agent.py)
    ```
    """)

    if not runs:
        st.warning("No agent execution logs recorded for this application.")
        return

    # Timeline view
    df_runs = pd.DataFrame(runs)
    total_ms = df_runs["duration_ms"].sum()
    st.metric("Total Workflow Execution Latency", f"{total_ms:,.2f} ms")

    for idx, run in enumerate(runs):
        status = run["status"]
        icon = "✅" if status == "SUCCESS" else "⚠️" if status == "WARNING" else "⏸️" if status == "PAUSED" else "❌"

        with st.expander(f"{icon} Step {idx+1}: **{run['agent_name']}** — {status} ({run['duration_ms']} ms)"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Workflow Trace ID**: `{run['workflow_trace_id']}`")
                st.write(f"**Execution Window**: `{run['start_time']}` to `{run['end_time']}`")
                st.write(f"**Input Reference**: {run.get('input_summary') or 'N/A'}")
            with c2:
                st.write(f"**Output Result**: {run.get('output_summary') or 'N/A'}")
                if run.get("escalation_reason"):
                    st.error(f"**Escalation / Halt Reason**: {run['escalation_reason']}")
                else:
                    st.success("Completed within normal operational boundaries.")
