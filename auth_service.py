"""
Authentication, Authorization and Role-Based Access Control (RBAC) Service.
Enforces strict server-side permissions for Applicants, Credit Officers,
Fraud Investigators, and Administrators.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from services.audit_service import AuditService

# Allowed roles
ROLE_APPLICANT = "Applicant"
ROLE_CREDIT_OFFICER = "Credit Officer"
ROLE_FRAUD_INVESTIGATOR = "Fraud Investigator"
ROLE_ADMINISTRATOR = "Administrator"

ALL_ROLES = [ROLE_CREDIT_OFFICER, ROLE_FRAUD_INVESTIGATOR, ROLE_ADMINISTRATOR, ROLE_APPLICANT]
STAFF_ROLES = [ROLE_CREDIT_OFFICER, ROLE_FRAUD_INVESTIGATOR, ROLE_ADMINISTRATOR]

# Permissions mapping
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    ROLE_APPLICANT: [
        "submit_application",
        "view_own_application",
        "upload_own_documents",
        "view_own_documents",
        "create_complaint",
        "view_own_complaints",
        "view_public_methodology",
    ],
    ROLE_CREDIT_OFFICER: [
        "view_dashboard",
        "view_all_applications",
        "review_applications",
        "verify_documents",
        "make_underwriting_decision",
        "view_agent_logs",
        "view_analytics",
        "view_complaints",
        "view_public_methodology",
        "view_staff_methodology_audit",
        "access_sandbox",
        "run_sandbox_scenarios",
    ],
    ROLE_FRAUD_INVESTIGATOR: [
        "view_dashboard",
        "view_all_applications",
        "view_fraud_cases",
        "update_fraud_cases",
        "inspect_document_tampering",
        "view_agent_logs",
        "view_analytics",
        "view_complaints",
        "view_public_methodology",
        "view_staff_methodology_audit",
        "access_sandbox",
        "run_sandbox_scenarios",
    ],
    ROLE_ADMINISTRATOR: [
        "view_dashboard",
        "view_all_applications",
        "review_applications",
        "view_fraud_cases",
        "update_fraud_cases",
        "manage_system_settings",
        "view_audit_logs",
        "view_agent_logs",
        "view_analytics",
        "view_complaints",
        "resolve_complaints",
        "view_public_methodology",
        "view_staff_methodology_audit",
        "access_sandbox",
        "run_sandbox_scenarios",
        "manage_sandbox_scenarios",
    ],
}


class AuthService:
    """Server-side access control validator and authorization logger."""

    @staticmethod
    def is_authorized(role: str, permission: str) -> bool:
        """Verify whether a given role possesses the specified permission."""
        perms = ROLE_PERMISSIONS.get(role, [])
        return permission in perms

    @staticmethod
    def is_staff(role: str) -> bool:
        """Check whether role belongs to authorized staff."""
        return role in STAFF_ROLES

    @staticmethod
    def validate_application_access(role: str, current_applicant_id: Optional[str], record_applicant_id: str) -> bool:
        """
        Ensure applicants can only access their own records,
        while staff can access all cases subject to role logging.
        """
        if AuthService.is_staff(role):
            return True
        if role == ROLE_APPLICANT:
            if not current_applicant_id or not record_applicant_id:
                return False
            return str(current_applicant_id).strip() == str(record_applicant_id).strip()
        return False

    # Standard Demonstration Credentials for each role
    DEMO_CREDENTIALS = {
        ROLE_CREDIT_OFFICER: {
            "user_id": "USR-CREDIT-01",
            "username": "officer",
            "email": "officer@creditflow.bank",
            "password": "password123",
            "full_name": "Priya Nair",
            "title": "Senior Credit Officer & Underwriter",
            "department": "Retail Credit Risk & Committees",
            "avatar": "👮‍♀️",
            "badge_color": "#2563EB"
        },
        ROLE_FRAUD_INVESTIGATOR: {
            "user_id": "USR-FRAUD-01",
            "username": "investigator",
            "email": "investigator@creditflow.bank",
            "password": "password123",
            "full_name": "Amitabh Sen",
            "title": "Lead Fraud & AML Investigator",
            "department": "Financial Crime & Security Operations",
            "avatar": "🕵️‍♂️",
            "badge_color": "#D97706"
        },
        ROLE_ADMINISTRATOR: {
            "user_id": "USR-ADMIN-01",
            "username": "admin",
            "email": "admin@creditflow.bank",
            "password": "password123",
            "full_name": "Dr. Vikram Seth",
            "title": "Chief Risk Officer & IT Administrator",
            "department": "Platform Governance & Compliance",
            "avatar": "🛡️",
            "badge_color": "#7C3AED"
        },
        ROLE_APPLICANT: {
            "user_id": "USR-APPLICANT-01",
            "username": "applicant",
            "email": "aarav.sharma@gmail.com",
            "password": "password123",
            "full_name": "Aarav Sharma",
            "title": "Retail Loan Applicant",
            "department": "Borrower Self-Service Portal",
            "avatar": "👤",
            "badge_color": "#059669"
        }
    }

    @classmethod
    def get_demo_user(cls, role: str) -> Dict[str, Any]:
        """Retrieve standard demo profile for a given role."""
        return cls.DEMO_CREDENTIALS.get(role, cls.DEMO_CREDENTIALS[ROLE_CREDIT_OFFICER])

    @classmethod
    def authenticate(cls, username: str, password: str, role_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Verify credentials for the target role.
        Accepts role-specific demo credentials or general demonstration passwords.
        """
        if not username or not password:
            return None

        u_clean = username.strip().lower()
        p_clean = password.strip()

        # Check in predefined credentials
        for role, creds in cls.DEMO_CREDENTIALS.items():
            if role_hint and role != role_hint:
                continue

            matches_user = (u_clean == creds["username"].lower() or u_clean == creds["email"].lower())
            valid_pw = (
                p_clean == creds["password"] or
                p_clean == f"{creds['username']}123" or
                p_clean == "password123" or
                p_clean == "admin123"
            )

            if matches_user and valid_pw:
                user_profile = creds.copy()
                user_profile["role"] = role
                user_profile["authenticated_at"] = datetime.utcnow().isoformat()
                return user_profile

        # Allow flexible custom registration / applicant login
        if role_hint == ROLE_APPLICANT and len(u_clean) >= 3 and len(p_clean) >= 4:
            import uuid
            return {
                "user_id": f"USR-APP-{uuid.uuid4().hex[:6].upper()}",
                "username": u_clean,
                "email": u_clean if "@" in u_clean else f"{u_clean}@borrower.in",
                "full_name": username.replace(".", " ").replace("@", " ").split()[0].title(),
                "role": ROLE_APPLICANT,
                "title": "Registered Retail Borrower",
                "department": "Borrower Self-Service Portal",
                "avatar": "👤",
                "badge_color": "#059669",
                "authenticated_at": datetime.utcnow().isoformat()
            }

        return None

    @classmethod
    def register_applicant(cls, full_name: str, email: str, phone: str, password: str) -> Optional[Dict[str, Any]]:
        """Register a new applicant account for demo exploration."""
        if not full_name or not email or len(password) < 4:
            return None
        import uuid
        return {
            "user_id": f"USR-APP-{uuid.uuid4().hex[:6].upper()}",
            "username": email.split("@")[0],
            "email": email.strip().lower(),
            "phone": phone.strip(),
            "full_name": full_name.strip(),
            "role": ROLE_APPLICANT,
            "title": "Registered Retail Borrower",
            "department": "Borrower Self-Service Portal",
            "avatar": "👤",
            "badge_color": "#059669",
            "authenticated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    def log_login_event(user_id: str, role: str, username: str):
        """Record an authenticated login event in audit logs."""
        AuditService.log_event(
            actor_id=user_id,
            actor_role=role,
            action="USER_LOGIN_SUCCESS",
            application_id=None,
            event_details={
                "username": username,
                "login_timestamp": datetime.utcnow().isoformat(),
                "auth_method": "ROLE_BASED_CREDENTIAL_PORTAL"
            }
        )

    @staticmethod
    def log_logout_event(user_id: str, role: str, username: str):
        """Record an explicit user logout event in audit logs."""
        AuditService.log_event(
            actor_id=user_id,
            actor_role=role,
            action="USER_LOGOUT",
            application_id=None,
            event_details={
                "username": username,
                "logout_timestamp": datetime.utcnow().isoformat()
            }
        )
