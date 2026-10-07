"""
Console Development Messaging Provider for ZeroGuard AI.
Simulates SMS and WhatsApp dispatches directly to stdout/logger for local development and demos.
"""
import logging
import uuid
from typing import Optional, Dict, Any
from backend.services.messaging.base import MessageProvider, MessageResult

logger = logging.getLogger(__name__)


class ConsoleProvider(MessageProvider):
    """Console simulation provider for zero-cost local testing and demos."""

    @property
    def name(self) -> str:
        return 'console'

    def send_sms(
        self,
        phone: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Prints SMS message to server logs."""
        masked_phone = phone[:4] + '******' + phone[-4:] if len(phone) >= 8 else '***'
        msg_id = f"CONSOLE-SMS-{uuid.uuid4().hex[:12].upper()}"

        print("\n" + "=" * 75)
        print("[ZEROGUARD AI DEV SMS DISPATCH]")
        print(f"To (E.164):  {phone} (Masked: {masked_phone})")
        print(f"Message ID:  {msg_id}")
        if template_id:
            print(f"DLT Template ID: {template_id}")
        print("-" * 75)
        safe_body = str(body).encode('ascii', errors='replace').decode('ascii')
        print(safe_body)
        print("=" * 75 + "\n")

        logger.info(f"[ConsoleProvider] Simulated SMS to {masked_phone} (ID: {msg_id})")

        return MessageResult(
            success=True,
            provider=self.name,
            channel='sms',
            provider_message_id=msg_id,
            status='delivered',
            raw_response={'simulated': True, 'msg_id': msg_id}
        )

    def send_whatsapp(
        self,
        phone: str,
        body: str,
        template_name: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Prints WhatsApp message to server logs."""
        masked_phone = phone[:4] + '******' + phone[-4:] if len(phone) >= 8 else '***'
        msg_id = f"CONSOLE-WA-{uuid.uuid4().hex[:12].upper()}"

        print("\n" + "=" * 75)
        print("[ZEROGUARD AI DEV WHATSAPP DISPATCH]")
        print(f"To (E.164):    {phone} (Masked: {masked_phone})")
        print(f"Message ID:    {msg_id}")
        if template_name:
            print(f"Meta Template: {template_name}")
        print("-" * 75)
        safe_body = str(body).encode('ascii', errors='replace').decode('ascii')
        print(safe_body)
        print("=" * 75 + "\n")

        logger.info(f"[ConsoleProvider] Simulated WhatsApp to {masked_phone} (ID: {msg_id})")

        return MessageResult(
            success=True,
            provider=self.name,
            channel='whatsapp',
            provider_message_id=msg_id,
            status='delivered',
            raw_response={'simulated': True, 'msg_id': msg_id}
        )

    def verify_webhook(
        self,
        request_headers: Dict[str, str],
        request_body: bytes,
        request_data: Dict[str, Any]
    ) -> bool:
        """Always accepts simulated webhook in console mode."""
        return True
