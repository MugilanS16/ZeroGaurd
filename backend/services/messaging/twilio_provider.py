"""
Twilio Messaging Provider Implementation for ZeroGuard AI.
Supports both SMS and WhatsApp dispatch, delivery tracking, and webhook signature validation.
"""
import logging
from typing import Optional, Dict, Any
from backend.services.messaging.base import MessageProvider, MessageResult

logger = logging.getLogger(__name__)


class TwilioProvider(MessageProvider):
    """Twilio SMS & WhatsApp Provider."""

    @property
    def name(self) -> str:
        return 'twilio'

    def _get_client(self):
        try:
            from twilio.rest import Client
            account_sid = self.config.get('TWILIO_ACCOUNT_SID')
            auth_token = self.config.get('TWILIO_AUTH_TOKEN')
            if not account_sid or not auth_token:
                logger.warning("[TwilioProvider] Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in configuration.")
                return None
            client = Client(account_sid, auth_token)
            if hasattr(client, 'http_client') and hasattr(client.http_client, 'timeout'):
                client.http_client.timeout = 5.0
            return client
        except ImportError:
            logger.error("[TwilioProvider] twilio package is not installed.")
            return None

    def send_sms(
        self,
        phone: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Dispatches an SMS via Twilio Messaging API."""
        masked_phone = phone[:4] + '******' + phone[-4:] if len(phone) >= 8 else '***'
        client = self._get_client()

        if not client:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='sms',
                status='failed',
                error="Twilio client not initialized (missing credentials in .env)."
            )

        from_number = self.config.get('TWILIO_PHONE_NUMBER')
        if not from_number:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='sms',
                status='failed',
                error="TWILIO_PHONE_NUMBER is not set."
            )

        try:
            logger.info(f"[TwilioProvider] Dispatching SMS to {masked_phone} from {from_number}")
            message = client.messages.create(
                to=phone,
                from_=from_number,
                body=body
            )
            return MessageResult(
                success=True,
                provider=self.name,
                channel='sms',
                provider_message_id=message.sid,
                status=message.status or 'queued',
                raw_response={'sid': message.sid, 'status': message.status}
            )
        except Exception as e:
            logger.error(f"[TwilioProvider] SMS dispatch error to {masked_phone}: {e}")
            return MessageResult(
                success=False,
                provider=self.name,
                channel='sms',
                status='failed',
                error=str(e)
            )

    def send_whatsapp(
        self,
        phone: str,
        body: str,
        template_name: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Dispatches a WhatsApp message via Twilio WhatsApp API."""
        masked_phone = phone[:4] + '******' + phone[-4:] if len(phone) >= 8 else '***'
        client = self._get_client()

        if not client:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='whatsapp',
                status='failed',
                error="Twilio client not initialized (missing credentials in .env)."
            )

        from_number = self.config.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        if not from_number.startswith('whatsapp:'):
            from_number = f"whatsapp:{from_number}"

        to_number = phone if phone.startswith('whatsapp:') else f"whatsapp:{phone}"

        try:
            logger.info(f"[TwilioProvider] Dispatching WhatsApp to {masked_phone} from {from_number}")
            message = client.messages.create(
                to=to_number,
                from_=from_number,
                body=body
            )
            return MessageResult(
                success=True,
                provider=self.name,
                channel='whatsapp',
                provider_message_id=message.sid,
                status=message.status or 'queued',
                raw_response={'sid': message.sid, 'status': message.status}
            )
        except Exception as e:
            logger.error(f"[TwilioProvider] WhatsApp dispatch error to {masked_phone}: {e}")
            return MessageResult(
                success=False,
                provider=self.name,
                channel='whatsapp',
                status='failed',
                error=str(e)
            )

    def verify_webhook(
        self,
        request_headers: Dict[str, str],
        request_body: bytes,
        request_data: Dict[str, Any]
    ) -> bool:
        """Validates Twilio webhook signatures using RequestValidator."""
        auth_token = self.config.get('TWILIO_AUTH_TOKEN')
        if not auth_token:
            return False

        signature = request_headers.get('X-Twilio-Signature') or request_headers.get('x-twilio-signature')
        if not signature:
            return False

        try:
            from twilio.request_validator import RequestValidator
            validator = RequestValidator(auth_token)
            url = request_headers.get('X-Original-URL') or request_headers.get('Host', '')
            return validator.validate(url, request_data, signature)
        except Exception as e:
            logger.warning(f"[TwilioProvider] Webhook verification exception: {e}")
            return False
