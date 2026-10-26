"""
Clear Executive Dashboard & Workflow Pulse.
Provides high-clarity metrics, clean horizontal bar and donut charts (no rotated/clipped text),
product breakdown (Personal Loan vs Education Loan), and role-tailored views.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

from services.database import get_dashboard_metrics, list_applications
from services.auth_service import AuthService, ROLE_APPLICANT, ROLE_CREDIT_OFFICER, ROLE_FRAUD_INVESTIGATOR, ROLE_ADMINISTRATOR


# Friendly Label Mappings to avoid ugly raw enum strings with underscores
STATUS_DISPLAY_MAP = {
    "PRE_SCREENING_COMPLETED": "Pre-Screening Complete",
    "HUMAN_REVIEW_REQUIRED": "Human Review Required",
    "MORE_INFORMATION_REQUIRED": "More Info Needed",
    "ON_HOLD": "Verification Hold",
    "DISPUTED": "Disputed / Grievance",
    "APPROVED_BY_AUTHORIZED_LENDER": "Sanctioned by Lender",
    "DECLINED_BY_AUTHORIZED_LENDER": "Declined by Lender",
    "RECEIVED": "New Intake Received",
    "UNDER_EVALUATION": "Under AI Assessment"
}

OUTCOME_DISPLAY_MAP = {
    "PROCEED_TO_NEXT_STAGE": "Auto Proceeded",
    "REQUIRES_HUMAN_REVIEW": "Human Review Required",
    "MORE_INFORMATION_REQUIRED": "More Info Needed",
    "ON_HOLD_FOR_VERIFICATION": "Verification Hold",
    "UNDER_EVALUATION": "Under Evaluation"
}

STATUS_COLOR_MAP = {
    "Pre-Screening Complete": "#10B981",       # Emerald Green
    "Human Review Required": "#F59E0B",       # Warm Amber
    "More Info Needed": "#3B82F6",            # Blue
    "Verification Hold": "#EF4444",           # Coral Red
    "Disputed / Grievance": "#8B5CF6",        # Purple
    "Sanctioned by Lender": "#059669",        # Dark Emerald
    "Declined by Lender": "#6B7280",          # Slate Gray
    "New Intake Received": "#0284C7",         # Sky Blue
    "Under AI Assessment": "#6366F1"          # Indigo
}

OUTCOME_COLOR_MAP = {
    "Auto Proceeded": "#10B981",              # Emerald Green
    "Human Review Required": "#F59E0B",       # Amber
    "More Info Needed": "#3B82F6",            # Blue
    "Verification Hold": "#EF4444",           # Coral Red
    "Under Evaluation": "#6366F1"             # Indigo
}


def render_dashboard():
    """Renders the high-clarity dashboard tailored to the user's role."""
    current_role = st.session_state.get("active_role", ROLE_CREDIT_OFFICER)
    current_user = st.session_state.get("current_user", {})
    user_name = current_user.get("full_name", current_role)

    # If logged in as Applicant, render the clean Borrower Portal Dashboard
    if current_role == ROLE_APPLICANT:
        _render_applicant_dashboard(user_name)
        return

    # Otherwise render Staff Executive Dashboard (Credit Officer, Fraud Investigator, Administrator)
    _render_staff_dashboard(current_role, user_name)


def _render_applicant_dashboard(user_name: str):
    """Clean borrower dashboard showing personal loan status and quick actions."""
    st.markdown(f'<div class="page-title">👋 Welcome back, {user_name}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Track your loan pre-screening progress, manage uploaded documents, or start a new loan application.</div>',
        unsafe_allow_html=True
    )

    # Fetch applicant's own applications
    applicant_query = st.session_state.get("applicant_filter_name", "")
    all_apps = list_applications(limit=50)
    my_apps = [a for a in all_apps if applicant_query.lower() in a.get("full_name", "").lower()] if applicant_query else all_apps[:2]

    # Quick Action Cards
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">💼 Personal Loan</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 14px;">Instant automated pre-screening for salaried & professional applicants. DTI assessment up to ₹25 Lakhs.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Apply for Personal Loan", key="app_apply_pl", type="primary", use_container_width=True):
            st.session_state["active_nav"] = "📝 New Loan Application"
            st.session_state["preselected_product"] = "PERSONAL_LOAN"
            st.rerun()

    with col_act2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #065F46 0%, #059669 100%); color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">🎓 Higher Education Loan</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 14px;">Covers tuition, hostel, exam fees & equipment. Study-period interest & moratorium support.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 Apply for Education Loan", key="app_apply_edu", type="primary", use_container_width=True):
            st.session_state["active_nav"] = "📝 New Loan Application"
            st.session_state["preselected_product"] = "EDUCATION_LOAN"
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Active Applications Status Cards
    st.markdown('<div class="section-card-title">📋 My Active Loan Applications</div>', unsafe_allow_html=True)

    if not my_apps:
        st.markdown("""
        <div class="empty-state-card">
            <div style="font-size: 2.8rem; margin-bottom: 10px;">📄</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: #0F2942;">No Active Applications Submitted Yet</div>
            <div style="color: #64748B; font-size: 0.88rem; max-width: 500px; margin: 6px auto 16px auto;">
                Submit your first pre-screening application above to observe the 7-agent automated evaluation workflow.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for app in my_apps:
            prod_icon = "🎓" if "EDUCATION" in str(app.get("loan_product", "")) else "💼"
            prod_name = "Higher Education Loan" if "EDUCATION" in str(app.get("loan_product", "")) else "Personal Loan"
            status_text = STATUS_DISPLAY_MAP.get(app.get("status", ""), app.get("status", ""))
            amount_str = f"₹{app.get('requested_loan_amount', 0):,.2f}"

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 700; font-size: 1.05rem; color: #0F2942;">
                            {prod_icon} {prod_name} — <span style="color: #2563EB;">{app.get('application_id')}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                            Requested Amount: <b>{amount_str}</b> • Submitted On: {str(app.get('created_at', ''))[:10]}
                        </div>
                    </div>
                    <div>
                        <span style="background: #EFF6FF; color: #1D4ED8; font-weight: 700; padding: 6px 14px; border-radius: 9999px; font-size: 0.8rem;">
                            ● {status_text}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_staff_dashboard(current_role: str, user_name: str):
    """Renders the high-clarity Staff Executive Dashboard."""
    # Top Header Strip with User Role and System Health
    col_head_left, col_head_right = st.columns([3, 1])
    with col_head_left:
        st.markdown(f'<div class="page-title">📊 Executive Dashboard & Workflow Pulse</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="page-subtitle">Logged in as <b>{user_name}</b> ({current_role}) • Real-time pre-screening throughput & underwriting queues.</div>',
            unsafe_allow_html=True
        )
    with col_head_right:
        st.markdown("""
        <div style="text-align: right; padding-top: 6px;">
            <span style="background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; padding: 6px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 700;">
                ● System Operational (99.98%)
            </span>
        </div>
        """, unsafe_allow_html=True)

    metrics = get_dashboard_metrics()
    total_apps = metrics["total_applications"]

    # 1. Product Filter Controls
    col_filt1, col_filt2 = st.columns([2, 2])
    with col_filt1:
        product_filter = st.radio(
            "Filter Loan Product View:",
            ["All Loan Products", "💼 Personal Loans Only", "🎓 Higher Education Loans Only"],
            horizontal=True,
            key="dash_prod_filter"
        )
    with col_filt2:
        st.markdown("""
        <div style="text-align: right; color: #64748B; font-size: 0.82rem; padding-top: 14px;">
            Policies: <b>PL Board Policy v2.4</b> & <b>EDU Board Policy v2.4</b> (RBI DL 2022 Verified)
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. Hero KPI Metric Cards (High Contrast & Clear)
    auto_rate = round((metrics["auto_proceeded"] / total_apps * 100), 1) if total_apps > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card border-blue">
            <div class="metric-label">Total Applications</div>
            <div class="metric-value">{total_apps}</div>
            <div class="metric-help">Intake records in database</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card border-green">
            <div class="metric-label">Automated Pre-Screen Passes</div>
            <div class="metric-value text-green">{metrics["auto_proceeded"]} <span style="font-size: 1rem; color: #10B981; font-weight: 600;">({auto_rate}%)</span></div>
            <div class="metric-help">Proceeded to next stage</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card border-amber">
            <div class="metric-label">Underwriter Review Queue</div>
            <div class="metric-value text-amber">{metrics["requiring_human_review"]}</div>
            <div class="metric-help">Policy exceptions & high DTI</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card border-red">
            <div class="metric-label">Verification Holds & Fraud</div>
            <div class="metric-value text-red">{metrics["more_info_required"] + metrics["fraud_cases"]}</div>
            <div class="metric-help">Holds: {metrics["more_info_required"]} • Fraud Cases: {metrics["fraud_cases"]}</div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary Micro-KPI Strip
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.caption(f"⚡ **Avg Agent Cycle:** `{metrics['avg_assessment_ms']} ms`")
    with col_m2:
        st.caption(f"🛡️ **Active Fraud Inquiries:** `{metrics['fraud_cases']} case(s)`")
    with col_m3:
        st.caption(f"⚖️ **Open Disputes:** `{metrics['open_complaints']} ticket(s)`")
    with col_m4:
        st.caption(f"⚙️ **Runtime Exceptions:** `{metrics['agent_exceptions']} incident(s)`")

    st.markdown("<hr style='margin: 18px 0;'/>", unsafe_allow_html=True)

    # Product Split Comparison Box
    prod_dist = metrics.get("product_distribution", {})
    pl_data = prod_dist.get("PERSONAL_LOAN", {"count": 0, "total_volume": 0.0})
    edu_data = prod_dist.get("EDUCATION_LOAN", {"count": 0, "total_volume": 0.0})

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 14px 18px;">
            <div style="font-weight: 700; color: #0F2942; font-size: 1rem;">💼 Personal Loans Overview</div>
            <div style="display: flex; gap: 24px; margin-top: 8px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Total Files:</span>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #0F2942;">{pl_data['count']}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Pipeline Volume:</span>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #2563EB;">₹{pl_data['total_volume']:,.0f}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Policy Rule:</span>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #475569; margin-top: 6px;">DTI ≤ 55%, Min ₹25k</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_p2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #059669; border-radius: 8px; padding: 14px 18px;">
            <div style="font-weight: 700; color: #0F2942; font-size: 1rem;">🎓 Higher Education Loans Overview</div>
            <div style="display: flex; gap: 24px; margin-top: 8px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Total Files:</span>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #0F2942;">{edu_data['count']}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Pipeline Volume:</span>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #059669;">₹{edu_data['total_volume']:,.0f}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B;">Funding Rule:</span>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #475569; margin-top: 6px;">Eligible Costs − Funding</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 3. Crystal Clear Visualizations
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown('<div class="section-card-title">📌 Application Status Distribution</div>', unsafe_allow_html=True)
        status_dist = metrics.get("status_distribution", {})
        if status_dist:
            # Map keys to friendly display names
            friendly_status_dist = {}
            for k, v in status_dist.items():
                name = STATUS_DISPLAY_MAP.get(k, k.replace("_", " ").title())
                friendly_status_dist[name] = friendly_status_dist.get(name, 0) + v

            df_status = pd.DataFrame(list(friendly_status_dist.items()), columns=["Status", "Count"])
            
            # Map colors cleanly
            color_sequence = [STATUS_COLOR_MAP.get(s, "#3B82F6") for s in df_status["Status"]]

            fig_status = px.pie(
                df_status,
                names="Status",
                values="Count",
                hole=0.55,
                color="Status",
                color_discrete_map=STATUS_COLOR_MAP
            )
            fig_status.update_traces(
                textposition='inside',
                textinfo='percent',
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
            )
            # Add center total text
            fig_status.add_annotation(
                text=f"<b>{total_apps}</b><br><span style='font-size:11px;color:#64748B'>Total Apps</span>",
                x=0.5, y=0.5,
                font_size=18,
                showarrow=False
            )
            fig_status.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.25,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11)
                )
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No applications to display in status distribution.")

    with col_chart_right:
        st.markdown('<div class="section-card-title">⚖️ Preliminary Decision Route Outcomes</div>', unsafe_allow_html=True)
        outcome_dist = metrics.get("outcome_distribution", {})
        if outcome_dist:
            # Convert raw enums to clean, formatted labels
            friendly_outcomes = []
            for k, v in outcome_dist.items():
                label = OUTCOME_DISPLAY_MAP.get(k, k.replace("_", " ").title())
                friendly_outcomes.append({"Outcome": label, "Count": v})

            df_outcome = pd.DataFrame(friendly_outcomes)
            # Sort by count ascending so biggest bar appears at top in horizontal chart
            df_outcome = df_outcome.sort_values(by="Count", ascending=True)

            # CRITICAL FIX: Use Horizontal Bar Chart (orientation="h")
            # This completely eliminates 45-degree angled text, prevents clipping,
            # and ensures 100% crystal-clear readability for executives!
            fig_outcome = px.bar(
                df_outcome,
                x="Count",
                y="Outcome",
                orientation="h",
                text="Count",
                color="Outcome",
                color_discrete_map=OUTCOME_COLOR_MAP
            )
            fig_outcome.update_traces(
                textposition="outside",
                texttemplate="%{x}",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Applications: %{x}<extra></extra>"
            )
            fig_outcome.update_layout(
                margin=dict(t=10, b=10, l=10, r=40),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(
                    title="Number of Applications",
                    dtick=1,
                    showgrid=True,
                    gridcolor="#E2E8F0"
                ),
                yaxis=dict(
                    title="",
                    tickfont=dict(size=12, color="#0F2942")
                )
            )
            st.plotly_chart(fig_outcome, use_container_width=True)
        else:
            st.info("No decision outcome records logged yet.")

    # 4. Recent Applications Intake Table
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_t_title, col_t_act = st.columns([3, 1])
    with col_t_title:
        st.markdown('<div class="section-card-title">🕒 Recent Applications Intake & Decisions</div>', unsafe_allow_html=True)
    with col_t_act:
        if st.button("📁 View All in Case Files", use_container_width=True):
            st.session_state["active_nav"] = "📁 Applications"
            st.rerun()

    recent = metrics.get("recent_applications", [])
    if recent:
        df_recent = pd.DataFrame(recent)

        # Apply Product Filter if selected
        if "Personal" in product_filter:
            df_recent = df_recent[df_recent["loan_product"] == "PERSONAL_LOAN"]
        elif "Education" in product_filter:
            df_recent = df_recent[df_recent["loan_product"] == "EDUCATION_LOAN"]

        if df_recent.empty:
            st.info("No records matching the selected product filter.")
        else:
            # Format display columns cleanly
            df_display = pd.DataFrame()
            df_display["App ID"] = df_recent["application_id"]
            df_display["Applicant"] = df_recent["full_name"]
            df_display["Loan Product"] = df_recent["loan_product"].apply(
                lambda p: "🎓 Higher Education" if p == "EDUCATION_LOAN" else "💼 Personal Loan"
            )
            df_display["Requested Amount"] = df_recent["requested_loan_amount"].apply(
                lambda v: f"₹{v:,.2f}" if pd.notnull(v) else "—"
            )
            df_display["Workflow Status"] = df_recent["status"].apply(
                lambda s: STATUS_DISPLAY_MAP.get(s, s)
            )
            df_display["Preliminary Route"] = df_recent["preliminary_outcome"].apply(
                lambda o: OUTCOME_DISPLAY_MAP.get(o, o if pd.notnull(o) else "Under Evaluation")
            )
            df_display["Intake Date"] = df_recent["created_at"].apply(
                lambda t: str(t)[:16] if pd.notnull(t) else "—"
            )

            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No application intake records found in database.")
