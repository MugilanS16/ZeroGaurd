"""
Abstract Base Classes and Data Structures for ZeroGuard AI Messaging Layer.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MessageResult:
    """Standardized response object for all messaging provider operations."""
    success: bool
    provider: str
    channel: str  # 'sms' or 'whatsapp'
    provider_message_id: Optional[str] = None
    status: str = 'queued'  # 'queued', 'sent', 'delivered', 'failed'
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'provider': self.provider,
            'channel': self.channel,
            'provider_message_id': self.provider_message_id,
            'status': self.status,
            'error': self.error
        }


class MessageProvider(ABC):
    """Abstract interface for third-party SMS and WhatsApp delivery services."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the provider (e.g. 'twilio', 'msg91', 'console')."""
        pass

    @abstractmethod
    def send_sms(
        self,
        phone: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Dispatches an SMS message to an E.164 phone number."""
        pass

    @abstractmethod
    def send_whatsapp(
        self,
        phone: str,
        body: str,
        template_name: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Dispatches a WhatsApp message to an E.164 phone number."""
        pass

    @abstractmethod
    def verify_webhook(
        self,
        request_headers: Dict[str, str],
        request_body: bytes,
        request_data: Dict[str, Any]
    ) -> bool:
        """Validates incoming delivery callback webhook signatures."""
        pass
