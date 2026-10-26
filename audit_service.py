"""
Audit service for tracking workflow actions, role-based transitions, and compliance events.
"""

import json
from typing import Dict, Any, Optional
from services.database import get_db_connection


class AuditService:
    @staticmethod
    def log_event(
        actor_id: str,
        actor_role: str,
        action: str,
        application_id: Optional[str] = None,
        event_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an immutable audit log entry."""
        try:
            conn = get_db_connection()
            with conn:
                conn.execute("""
                INSERT INTO audit_logs (application_id, actor_id, actor_role, action, event_details_json)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    application_id,
                    actor_id,
                    actor_role,
                    action,
                    json.dumps(event_details or {})
                ))
            conn.close()
            return True
        except Exception:
            return False
