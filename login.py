"""
Login and Authentication Gateway for CreditFlow AI.
Provides dedicated role-based login forms, quick demonstration credentials,
applicant registration, and secure logout handlers for each role:
- Credit Officer
- Fraud Investigator
- Administrator
- Applicant
"""

import streamlit as st
from datetime import datetime
from services.auth_service import (
    AuthService,
    ROLE_CREDIT_OFFICER,
    ROLE_FRAUD_INVESTIGATOR,
    ROLE_ADMINISTRATOR,
    ROLE_APPLICANT
)


def render_login_portal():
    """Renders the comprehensive multi-role login interface."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 28px; padding-top: 10px;">
        <div style="font-size: 2.8rem; margin-bottom: 6px;">🛡️</div>
        <div style="font-size: 1.9rem; font-weight: 800; color: #0F2942;">CreditFlow AI Authentication Gateway</div>
        <div style="font-size: 0.95rem; color: #64748B; max-width: 650px; margin: 0 auto;">
            Secure multi-agent pre-screening system with strict role-based access control (RBAC).
            Please sign in using your designated role credentials or one-click evaluation access.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Role Tabs for Login
    tab_officer, tab_investigator, tab_admin, tab_applicant = st.tabs([
        "👮 Credit Officer",
        "🕵️ Fraud Investigator",
        "🛡️ Administrator",
        "👤 Applicant / Borrower"
    ])

    # 1. Credit Officer Tab
    with tab_officer:
        st.markdown("""
        <div style="background: #EFF6FF; border-left: 4px solid #2563EB; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
            <strong style="color: #1E40AF;">Underwriter Portal:</strong> Review escalated files, inspect financial metrics, assess document validity, and record binding committee decisions.
        </div>
        """, unsafe_allow_html=True)

        col_form, col_quick = st.columns([3, 2])
        with col_form:
            with st.form("form_login_officer"):
                st.subheader("Credit Officer Login")
                u_off = st.text_input("Username or Email", value="officer", key="login_u_off", placeholder="officer or officer@creditflow.bank")
                p_off = st.text_input("Password", value="password123", type="password", key="login_p_off", placeholder="Enter password")
                remember_me = st.checkbox("Keep me signed in for this session", value=True, key="rem_off")
                submit_off = st.form_submit_button("🔐 Sign In as Credit Officer", type="primary", use_container_width=True)

                if submit_off:
                    user = AuthService.authenticate(u_off, p_off, role_hint=ROLE_CREDIT_OFFICER)
                    if user:
                        _login_user(user)
                    else:
                        st.error("Invalid credentials. Use demo username 'officer' and password 'password123'.")

        with col_quick:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-top: 10px;">
                <div style="font-weight: 700; color: #0F2942; margin-bottom: 6px;">⚡ Quick Evaluator Access</div>
                <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 12px;">Instant 1-click access for academic evaluation:</div>
                <div style="font-size: 0.78rem; font-family: monospace; background: #F8FAFC; padding: 6px 10px; border-radius: 4px; margin-bottom: 12px;">
                    User: <b>officer</b><br>
                    Pass: <b>password123</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 1-Click Login (Credit Officer)", key="quick_btn_officer", use_container_width=True):
                demo_user = AuthService.get_demo_user(ROLE_CREDIT_OFFICER)
                _login_user(demo_user)

    # 2. Fraud Investigator Tab
    with tab_investigator:
        st.markdown("""
        <div style="background: #FFFBEB; border-left: 4px solid #D97706; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
            <strong style="color: #92400E;">Fraud Investigation Portal:</strong> Inspect tamper flags, verify entity mismatch traces, manage escalated suspicious applications, and record resolution notes.
        </div>
        """, unsafe_allow_html=True)

        col_form, col_quick = st.columns([3, 2])
        with col_form:
            with st.form("form_login_investigator"):
                st.subheader("Fraud Investigator Login")
                u_inv = st.text_input("Username or Email", value="investigator", key="login_u_inv", placeholder="investigator or investigator@creditflow.bank")
                p_inv = st.text_input("Password", value="password123", type="password", key="login_p_inv", placeholder="Enter password")
                st.checkbox("Keep me signed in for this session", value=True, key="rem_inv")
                submit_inv = st.form_submit_button("🔐 Sign In as Fraud Investigator", type="primary", use_container_width=True)

                if submit_inv:
                    user = AuthService.authenticate(u_inv, p_inv, role_hint=ROLE_FRAUD_INVESTIGATOR)
                    if user:
                        _login_user(user)
                    else:
                        st.error("Invalid credentials. Use demo username 'investigator' and password 'password123'.")

        with col_quick:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-top: 10px;">
                <div style="font-weight: 700; color: #0F2942; margin-bottom: 6px;">⚡ Quick Evaluator Access</div>
                <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 12px;">Instant 1-click access for academic evaluation:</div>
                <div style="font-size: 0.78rem; font-family: monospace; background: #F8FAFC; padding: 6px 10px; border-radius: 4px; margin-bottom: 12px;">
                    User: <b>investigator</b><br>
                    Pass: <b>password123</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 1-Click Login (Fraud Investigator)", key="quick_btn_inv", use_container_width=True):
                demo_user = AuthService.get_demo_user(ROLE_FRAUD_INVESTIGATOR)
                _login_user(demo_user)

    # 3. Administrator Tab
    with tab_admin:
        st.markdown("""
        <div style="background: #F5F3FF; border-left: 4px solid #7C3AED; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
            <strong style="color: #5B21B6;">System Administrator Portal:</strong> Oversee full system audit logs, configure lending policies, manage model parameters, and access the protected sandbox.
        </div>
        """, unsafe_allow_html=True)

        col_form, col_quick = st.columns([3, 2])
        with col_form:
            with st.form("form_login_admin"):
                st.subheader("System Administrator Login")
                u_adm = st.text_input("Username or Email", value="admin", key="login_u_adm", placeholder="admin or admin@creditflow.bank")
                p_adm = st.text_input("Password", value="password123", type="password", key="login_p_adm", placeholder="Enter password")
                st.checkbox("Keep me signed in for this session", value=True, key="rem_adm")
                submit_adm = st.form_submit_button("🔐 Sign In as Administrator", type="primary", use_container_width=True)

                if submit_adm:
                    user = AuthService.authenticate(u_adm, p_adm, role_hint=ROLE_ADMINISTRATOR)
                    if user:
                        _login_user(user)
                    else:
                        st.error("Invalid credentials. Use demo username 'admin' and password 'password123'.")

        with col_quick:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-top: 10px;">
                <div style="font-weight: 700; color: #0F2942; margin-bottom: 6px;">⚡ Quick Evaluator Access</div>
                <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 12px;">Instant 1-click access for academic evaluation:</div>
                <div style="font-size: 0.78rem; font-family: monospace; background: #F8FAFC; padding: 6px 10px; border-radius: 4px; margin-bottom: 12px;">
                    User: <b>admin</b><br>
                    Pass: <b>password123</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 1-Click Login (Administrator)", key="quick_btn_admin", use_container_width=True):
                demo_user = AuthService.get_demo_user(ROLE_ADMINISTRATOR)
                _login_user(demo_user)

    # 4. Applicant Tab
    with tab_applicant:
        st.markdown("""
        <div style="background: #ECFDF5; border-left: 4px solid #059669; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
            <strong style="color: #065F46;">Borrower Self-Service Portal:</strong> Submit personal and education loan pre-screenings, upload itemized costs, track verification stages, and review decisions.
        </div>
        """, unsafe_allow_html=True)

        app_login_mode = st.radio("Choose Option", ["Sign In as Existing Borrower", "Register New Borrower Account"], horizontal=True)

        if app_login_mode == "Sign In as Existing Borrower":
            col_form, col_quick = st.columns([3, 2])
            with col_form:
                with st.form("form_login_applicant"):
                    st.subheader("Borrower Account Login")
                    u_app = st.text_input("Borrower Email or Username", value="applicant", key="login_u_app", placeholder="applicant or email@domain.com")
                    p_app = st.text_input("Password", value="password123", type="password", key="login_p_app", placeholder="Enter password")
                    submit_app = st.form_submit_button("🔐 Sign In as Applicant", type="primary", use_container_width=True)

                    if submit_app:
                        user = AuthService.authenticate(u_app, p_app, role_hint=ROLE_APPLICANT)
                        if user:
                            _login_user(user)
                        else:
                            st.error("Invalid credentials. Use demo username 'applicant' and password 'password123'.")

            with col_quick:
                st.markdown("""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-top: 10px;">
                    <div style="font-weight: 700; color: #0F2942; margin-bottom: 6px;">⚡ Quick Evaluator Access</div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 12px;">Instant 1-click access for academic evaluation:</div>
                    <div style="font-size: 0.78rem; font-family: monospace; background: #F8FAFC; padding: 6px 10px; border-radius: 4px; margin-bottom: 12px;">
                        User: <b>applicant</b><br>
                        Pass: <b>password123</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🚀 1-Click Login (Applicant)", key="quick_btn_applicant", use_container_width=True):
                    demo_user = AuthService.get_demo_user(ROLE_APPLICANT)
                    _login_user(demo_user)

        else:
            with st.form("form_register_applicant"):
                st.subheader("New Borrower Registration")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    reg_name = st.text_input("Full Legal Name", placeholder="e.g. Aarav Sharma")
                    reg_email = st.text_input("Email Address", placeholder="e.g. aarav@example.com")
                with col_r2:
                    reg_phone = st.text_input("Mobile Phone (10 digits)", placeholder="e.g. 9876543210")
                    reg_pw = st.text_input("Create Password", type="password", placeholder="Min 4 characters")

                agree_consent = st.checkbox("I agree to data processing in accordance with CreditFlow Privacy & Academic Policies", value=True)
                submit_reg = st.form_submit_button("✨ Complete Registration & Sign In", type="primary", use_container_width=True)

                if submit_reg:
                    if not agree_consent:
                        st.warning("Please agree to the privacy policy to proceed.")
                    else:
                        reg_user = AuthService.register_applicant(reg_name, reg_email, reg_phone, reg_pw)
                        if reg_user:
                            st.success("Account registered successfully! Logging you in...")
                            _login_user(reg_user)
                        else:
                            st.error("Please fill in all registration fields with valid values.")


def _login_user(user: dict):
    """Establishes an authenticated user session in Streamlit state."""
    st.session_state["authenticated"] = True
    st.session_state["current_user"] = user
    st.session_state["active_role"] = user["role"]
    if user["role"] == ROLE_APPLICANT:
        st.session_state["applicant_filter_name"] = user["full_name"]
    else:
        st.session_state.pop("applicant_filter_name", None)

    # Default navigation based on role
    if "active_nav" not in st.session_state or st.session_state["active_nav"] == "🔐 Sign In":
        st.session_state["active_nav"] = "📊 Dashboard"

    # Audit log the authentication
    AuthService.log_login_event(
        user_id=user["user_id"],
        role=user["role"],
        username=user["username"]
    )

    st.toast(f"✅ Signed in as {user['full_name']} ({user['role']})", icon="🛡️")
    st.rerun()


def logout_user():
    """Logs out the active user and clears session state."""
    current_user = st.session_state.get("current_user")
    if current_user:
        AuthService.log_logout_event(
            user_id=current_user.get("user_id", "UNKNOWN"),
            role=current_user.get("role", "UNKNOWN"),
            username=current_user.get("username", "UNKNOWN")
        )

    st.session_state["authenticated"] = False
    st.session_state.pop("current_user", None)
    st.session_state["active_role"] = ROLE_APPLICANT
    st.session_state["active_nav"] = "📊 Dashboard"
    st.session_state.pop("applicant_filter_name", None)

    st.toast("👋 You have been logged out securely.", icon="🚪")
    st.rerun()


def render_sidebar_user_profile():
    """Renders the user profile card and logout button in the sidebar."""
    if not st.session_state.get("authenticated", False):
        st.markdown("""
        <div style="background: #F1F5F9; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 12px; margin-bottom: 14px; text-align: center;">
            <div style="font-size: 0.85rem; font-weight: 600; color: #475569;">Guest / Evaluation Session</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 2px;">Sign in below to unlock role permissions.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    user = st.session_state.get("current_user", {})
    full_name = user.get("full_name", "Authorized User")
    role = user.get("role", ROLE_CREDIT_OFFICER)
    title = user.get("title", "Staff Member")
    email = user.get("email", "")
    avatar = user.get("avatar", "👤")
    badge_color = user.get("badge_color", "#2563EB")

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <div style="font-size: 1.8rem; background: #F8FAFC; border-radius: 50%; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; border: 1px solid #E2E8F0;">
                {avatar}
            </div>
            <div style="overflow: hidden;">
                <div style="font-weight: 700; color: #0F2942; font-size: 0.92rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {full_name}
                </div>
                <div style="font-size: 0.72rem; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {title}
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
            <span style="display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; background: {badge_color}15; color: {badge_color};">
                ● {role}
            </span>
            <span style="font-size: 0.7rem; color: #10B981; font-weight: 600;">Active 🟢</span>
        </div>
        <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 6px; font-family: monospace;">
            {email}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Prominent Logout and Switch Role Buttons
    col_out, col_sw = st.columns([1, 1])
    with col_out:
        if st.button("🚪 Log Out", key="sidebar_logout_btn", type="secondary", use_container_width=True):
            logout_user()
    with col_sw:
        if st.button("🔄 Switch", key="sidebar_switch_btn", help="Switch to another role or account", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
