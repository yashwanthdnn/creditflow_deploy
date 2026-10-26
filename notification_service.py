"""
Notification dispatch service (SMS, Email, and in-app system alerts).
Records simulated dispatches into the SQLite notifications table.
"""

import logging
from typing import Optional
from services.database import get_db_connection

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def send_notification(
        recipient: str,
        subject: str,
        message: str,
        channel: str = "EMAIL",
        application_id: Optional[str] = None
    ) -> bool:
        """
        Send a notification to an applicant or credit officer.
        In the academic prototype, this logs to the database with SIMULATED status.
        """
        try:
            conn = get_db_connection()
            with conn:
                conn.execute("""
                INSERT INTO notifications (application_id, recipient, channel, subject, message, status)
                VALUES (?, ?, ?, ?, ?, 'SENT_SIMULATED')
                """, (application_id, recipient, channel, subject, message))
            conn.close()
            logger.info(f"[SIMULATED NOTIFICATION] Sent {channel} to {recipient}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to record notification: {e}")
            return False
