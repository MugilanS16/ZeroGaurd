"""
ZeroGuard AI Provider-Agnostic Messaging Package
Supports SMS and WhatsApp dispatch across Twilio, MSG91, and Console (Dev).
"""
from backend.services.messaging.base import MessageProvider, MessageResult
from backend.services.messaging.factory import get_messaging_provider

__all__ = ['MessageProvider', 'MessageResult', 'get_messaging_provider']
