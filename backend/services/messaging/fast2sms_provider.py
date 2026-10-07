"""
Fast2SMS Provider Implementation for ZeroGuard AI.
Direct OTP SMS Delivery to Indian Mobile Numbers using Fast2SMS API.
"""
import urllib.request
import urllib.parse
import json
import logging
from typing import Optional, Dict, Any
from backend.services.messaging.base import MessageProvider, MessageResult

logger = logging.getLogger(__name__)


class Fast2SMSProvider(MessageProvider):
    """Fast2SMS Indian SMS Provider for instant real mobile SMS OTP delivery."""

    @property
    def name(self) -> str:
        return 'fast2sms'

    def send_sms(
        self,
        phone: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Sends real SMS to Indian mobile number via Fast2SMS."""
        api_key = self.config.get('FAST2SMS_API_KEY', '').strip()
        if not api_key:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='sms',
                status='failed',
                error="FAST2SMS_API_KEY is not set in .env."
            )

        # Extract 10-digit Indian number
        clean_number = "".join(filter(str.isdigit, phone))
        if clean_number.startswith('91') and len(clean_number) == 12:
            clean_number = clean_number[2:]

        if len(clean_number) != 10:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='sms',
                status='failed',
                error="Fast2SMS requires a valid 10-digit Indian mobile number."
            )

        otp_val = (variables or {}).get('otp') or (variables or {}).get('1')
        if not otp_val:
            import re
            match = re.search(r'\b\d{6}\b', body)
            otp_val = match.group(0) if match else "123456"

        masked = f"+91******{clean_number[-4:]}"
        try:
            logger.info(f"[Fast2SMSProvider] Dispatching real SMS OTP to {masked}...")
            url = "https://www.fast2sms.com/dev/bulkV2"
            data = urllib.parse.urlencode({
                'authorization': api_key,
                'route': 'otp',
                'variables_values': otp_val,
                'numbers': clean_number,
                'flash': '0'
            }).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Cache-Control': 'no-cache'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=8.0) as response:
                resp_text = response.read().decode('utf-8')
                resp_json = json.loads(resp_text)
                
                if resp_json.get('return') is True or resp_json.get('status_code') == 200:
                    req_id = resp_json.get('request_id', 'FAST2SMS_SENT')
                    logger.info(f"[Fast2SMSProvider] SMS successfully sent to {masked} (Request ID: {req_id})")
                    return MessageResult(
                        success=True,
                        provider=self.name,
                        channel='sms',
                        provider_message_id=str(req_id),
                        status='sent',
                        raw_response=resp_json
                    )
                else:
                    err_msg = resp_json.get('message', ['Failed to send via Fast2SMS'])[0] if isinstance(resp_json.get('message'), list) else str(resp_json.get('message', 'Failed'))
                    logger.error(f"[Fast2SMSProvider] Fast2SMS error: {err_msg}")
                    return MessageResult(
                        success=False,
                        provider=self.name,
                        channel='sms',
                        status='failed',
                        error=err_msg,
                        raw_response=resp_json
                    )
        except Exception as e:
            logger.error(f"[Fast2SMSProvider] Connection error sending to {masked}: {e}")
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
        # Fast2SMS is SMS-only; fallback to send_sms
        return self.send_sms(phone=phone, body=body, variables=variables)

    def verify_webhook(
        self,
        request_headers: Dict[str, str],
        request_body: bytes,
        request_data: Dict[str, Any]
    ) -> bool:
        return True
