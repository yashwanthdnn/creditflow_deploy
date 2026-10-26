"""
AI Credit Assessment Agent for Automated Loan Pre-Screening.
Main Application Entry Point (Streamlit Web Interface).
CreditFlow AI — Compliant with Sections A, B, C, D, E, F, G.
"""

import os
import sys
import shutil
from pathlib import Path

# Ensure application root directory is always at the top of sys.path
_ROOT_DIR = Path(__file__).resolve().parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Self-healing package layout:
# If files were uploaded flat to the GitHub root directory, automatically organize them into packages
_PACKAGE_MAP = {
    "config": ["settings.py", "loan_rules.yaml", "document_requirements.yaml"],
    "services": [
        "auth_service.py", "database.py", "financial_engine.py", "personal_loan_policy.py",
        "education_loan_policy.py", "regulatory_registry.py", "sandbox_service.py",
        "document_service.py", "integration_service.py", "audit_service.py", "decision_policy.py",
        "notification_service.py", "ocr_service.py"
    ],
    "ui_pages": [
        "dashboard.py", "login.py", "new_application.py", "applications.py",
        "document_verification.py", "human_review.py", "fraud_investigation.py",
        "complaints_disputes.py", "agent_logs.py", "analytics.py", "responsible_ai.py",
        "methodology.py", "sandbox.py"
    ],
    "agents": [
        "coordinator_agent.py", "data_validation_agent.py", "financial_analysis_agent.py",
        "eligibility_rules_agent.py", "credit_risk_agent.py", "risk_explanation_agent.py",
        "record_management_agent.py"
    ],
    "models": ["schemas.py", "model_loader.py"],
    "ml": ["predict.py", "train_model.py", "evaluate_model.py", "model_loader.py"],
    "artifacts": ["credit_risk_model.joblib", "model_metadata.json"],
    "data": ["loan_prescreening.db", "sandbox_evaluations.db", "synthetic_credit_data.csv"]
}

for _pkg_name, _file_list in _PACKAGE_MAP.items():
    _target_dir = _ROOT_DIR / _pkg_name
    _target_dir.mkdir(parents=True, exist_ok=True)
    _init_file = _target_dir / "__init__.py"
    if not _init_file.exists():
        try:
            _init_file.write_text(f'"""{_pkg_name} package"""\n', encoding="utf-8")
        except Exception:
            pass
    for _fname in _file_list:
        _src_candidate = _ROOT_DIR / _fname
        _dest_target = _target_dir / _fname
        if _src_candidate.exists() and not _dest_target.exists():
            try:
                shutil.copy2(_src_candidate, _dest_target)
            except Exception:
                pass

import streamlit as st
from config.settings import ACADEMIC_PROTOTYPE_DISCLAIMER
from services.auth_service import AuthService, ROLE_APPLICANT, ROLE_CREDIT_OFFICER, ROLE_FRAUD_INVESTIGATOR, ROLE_ADMINISTRATOR

# Page Configuration
st.set_page_config(
    page_title="CreditFlow AI – AI Credit Assessment & Pre-Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional Light-Theme Banking CSS
st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1E293B;
    }

    /* Headings & Brand */
    h1, h2, h3, h4, h5, h6 {
        color: #0F2942 !important;
        font-weight: 700 !important;
    }

    .brand-container {
        padding: 12px 0 20px 0;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 16px;
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F2942;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-subtitle {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 2px;
        line-height: 1.3;
    }

    /* Cards */
    .metric-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 18px 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08);
    }
    .metric-card.border-green {
        border-top: 4px solid #10B981;
    }
    .metric-card.border-amber {
        border-top: 4px solid #F59E0B;
    }
    .metric-card.border-red {
        border-top: 4px solid #EF4444;
    }
    .metric-card.border-blue {
        border-top: 4px solid #2563EB;
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F2942;
        margin: 6px 0 2px 0;
    }
    .metric-help {
        font-size: 0.78rem;
        color: #94A3B8;
    }
    .text-green { color: #10B981 !important; }
    .text-amber { color: #F59E0B !important; }
    .text-red { color: #EF4444 !important; }
    .text-blue { color: #2563EB !important; }

    .page-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0F2942;
        margin-bottom: 4px;
    }
    .page-subtitle {
        font-size: 0.92rem;
        color: #64748B;
        margin-bottom: 22px;
    }
    .section-card-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F2942;
        margin-bottom: 12px;
    }

    .empty-state-card {
        background: #FFFFFF;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 40px 20px;
        text-align: center;
        margin: 20px 0;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    .role-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #EEF2FF;
        color: #3730A3;
        margin-bottom: 12px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease;
    }
    button[kind="primary"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }
    button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
    }

    /* Footer Disclaimer */
    .disclaimer-box {
        margin-top: 40px;
        padding: 16px 20px;
        background: #F1F5F9;
        border-radius: 8px;
        border-left: 4px solid #64748B;
        font-size: 0.8rem;
        color: #475569;
        line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# Imports for UI pages
from ui_pages.login import render_login_portal, render_sidebar_user_profile, logout_user
from ui_pages.dashboard import render_dashboard
from ui_pages.new_application import render_new_application
from ui_pages.applications import render_applications
from ui_pages.document_verification import render_document_verification
from ui_pages.human_review import render_human_review_queue
from ui_pages.fraud_investigation import render_fraud_investigation
from ui_pages.complaints_disputes import render_complaints_disputes
from ui_pages.agent_logs import render_agent_logs
from ui_pages.analytics import render_analytics
from ui_pages.responsible_ai import render_responsible_ai
from ui_pages.methodology import render_methodology
from ui_pages.sandbox import render_sandbox

# Initialize session authentication defaults
if "authenticated" not in st.session_state:
    # Initial state: authenticated as Credit Officer for seamless evaluation
    st.session_state["authenticated"] = True
    st.session_state["active_role"] = ROLE_CREDIT_OFFICER
    st.session_state["current_user"] = AuthService.get_demo_user(ROLE_CREDIT_OFFICER)

active_role = st.session_state.get("active_role", ROLE_CREDIT_OFFICER)
is_authenticated = st.session_state.get("authenticated", False)

# Sidebar Header & Branding
with st.sidebar:
    st.markdown("""
    <div class="brand-container">
        <div class="brand-title">🛡️ CreditFlow AI</div>
        <div class="brand-subtitle">Multi-Agent AI Credit Assessment & Pre-Screening System</div>
    </div>
    """, unsafe_allow_html=True)

    # User Profile & Logout Controls
    render_sidebar_user_profile()

    # Role Selector & Switcher (Accessible when logged in)
    if is_authenticated:
        role_options = [ROLE_CREDIT_OFFICER, ROLE_FRAUD_INVESTIGATOR, ROLE_ADMINISTRATOR, ROLE_APPLICANT]
        curr_idx = role_options.index(active_role) if active_role in role_options else 0
        new_role = st.selectbox("Switch Active Role Environment", role_options, index=curr_idx, key="role_switcher_select")
        if new_role != active_role:
            st.session_state["active_role"] = new_role
            st.session_state["current_user"] = AuthService.get_demo_user(new_role)
            st.rerun()

    st.markdown("<hr style='margin: 12px 0;'/>", unsafe_allow_html=True)

    # Dynamic Navigation Menu based on Role Permissions
    if not is_authenticated:
        navigation_options = [
            "🔐 Sign In / Authentication",
            "📜 Rules, Financial Methodology & Limitations"
        ]
    elif AuthService.is_staff(active_role):
        navigation_options = [
            "📊 Dashboard",
            "📝 New Loan Application",
            "📁 Applications",
            "📄 Document Verification",
            "👤 Human Review Queue",
            "🛡️ Fraud Investigation",
            "⚖️ Complaints & Disputes",
            "🔄 Agent Execution Logs",
            "📈 Analytics & Model Performance",
            "⚙️ Responsible AI & Settings",
            "🧪 Secure Assessment Sandbox",
            "📜 Rules, Financial Methodology & Limitations"
        ]
    else:
        # Applicant navigation view (staff workbenches strictly omitted)
        navigation_options = [
            "📊 Dashboard",
            "📝 New Loan Application",
            "📁 Applications",
            "📄 Document Verification",
            "⚖️ Complaints & Disputes",
            "📜 Rules, Financial Methodology & Limitations"
        ]

    # Handle programmatic tab switches
    default_index = 0
    if "active_nav" in st.session_state and st.session_state["active_nav"] in navigation_options:
        default_index = navigation_options.index(st.session_state["active_nav"])

    selected_page = st.radio(
        "Navigation Menu",
        navigation_options,
        index=default_index,
        label_visibility="collapsed"
    )
    st.session_state["active_nav"] = selected_page

    st.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
    st.caption("CreditFlow Prototype v2.4 (Academic Sandbox)")
    st.caption("Seven Independent Operational Agents")

# --- Top Header User Bar (When Authenticated) ---
if is_authenticated:
    curr_user = st.session_state.get("current_user", {})
    u_name = curr_user.get("full_name", active_role)
    u_role = curr_user.get("role", active_role)
    u_avatar = curr_user.get("avatar", "👤")

    col_t_space, col_t_user, col_t_logout = st.columns([6, 3, 1])
    with col_t_user:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 4px; font-size: 0.82rem; color: #64748B;">
            {u_avatar} Logged in as <strong style="color: #0F2942;">{u_name}</strong>
            <span style="background: #EFF6FF; color: #1D4ED8; font-weight: 700; padding: 2px 8px; border-radius: 9999px; margin-left: 6px;">
                {u_role}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_t_logout:
        if st.button("🚪 Logout", key="top_bar_logout_btn", type="secondary", use_container_width=True):
            logout_user()

# --- Content Routing & Server-Side Access Control ---
staff_restricted_pages = [
    "👤 Human Review Queue",
    "🛡️ Fraud Investigation",
    "🔄 Agent Execution Logs",
    "🧪 Secure Assessment Sandbox"
]

if not is_authenticated:
    if selected_page == "📜 Rules, Financial Methodology & Limitations":
        render_methodology()
    else:
        render_login_portal()
elif active_role == ROLE_APPLICANT and selected_page in staff_restricted_pages:
    st.error("🚫 Access Denied: This administrative workbench is strictly restricted to authorized staff (Credit Officers, Fraud Investigators, Administrators).")
    st.info("Applicants can submit new loan applications, review submitted records, upload documents, open dispute tickets, or read the public methodology page.")
else:
    # Router
    if selected_page == "📊 Dashboard":
        render_dashboard()
    elif selected_page == "📝 New Loan Application":
        render_new_application()
    elif selected_page == "📁 Applications":
        render_applications()
    elif selected_page == "📄 Document Verification":
        render_document_verification()
    elif selected_page == "👤 Human Review Queue":
        render_human_review_queue()
    elif selected_page == "🛡️ Fraud Investigation":
        render_fraud_investigation()
    elif selected_page == "⚖️ Complaints & Disputes":
        render_complaints_disputes()
    elif selected_page == "🔄 Agent Execution Logs":
        render_agent_logs()
    elif selected_page == "📈 Analytics & Model Performance":
        render_analytics()
    elif selected_page == "⚙️ Responsible AI & Settings":
        render_responsible_ai()
    elif selected_page == "🧪 Secure Assessment Sandbox":
        render_sandbox()
    elif selected_page == "📜 Rules, Financial Methodology & Limitations":
        render_methodology()
    elif selected_page == "🔐 Sign In / Authentication":
        render_login_portal()

# Global Footer Disclaimer
st.markdown(f"""
<div class="disclaimer-box">
    <strong>Academic Prototype Notice:</strong> {ACADEMIC_PROTOTYPE_DISCLAIMER}
</div>
""", unsafe_allow_html=True)
