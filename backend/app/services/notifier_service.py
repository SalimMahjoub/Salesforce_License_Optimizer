"""
Notification Service with multiple channels (Slack, Email, Audit).

Implements notification routing and delivery management.
"""
import logging
from typing import List, Optional
from abc import ABC, abstractmethod
from datetime import datetime

import httpx
from app.config import get_settings
from app.events.event_bus import Event, EventType
from app.models.db.security_alert import SecurityAlert

logger = logging.getLogger(__name__)
settings = get_settings()


class Notifier(ABC):
    """Abstract base class for notifiers."""
    
    @abstractmethod
    async def send(self, message: dict) -> bool:
        """
        Send notification.
        
        Args:
            message: Notification payload
            
        Returns:
            True if successful
        """
        pass


class SlackNotifier(Notifier):
    """
    Slack notification channel.
    
    Sends formatted messages to Slack webhooks.
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
    
    async def send(self, message: dict) -> bool:
        """Send message to Slack."""
        try:
            payload = self._format_slack_message(message)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _format_slack_message(self, message: dict) -> dict:
        """Format message for Slack."""
        severity = message.get("severity", "MEDIUM")
        emoji = {
            "CRITICAL": ":rotating_light:",
            "HIGH": ":warning:",
            "MEDIUM": ":large_blue_circle:",
            "LOW": ":information_source:"
        }.get(severity, ":bell:")
        
        return {
            "text": f"{emoji} *{message.get('title')}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": message.get("title", "Notification")
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message.get("description", "")
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Sévérité:*\n{severity}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{message.get('timestamp', datetime.utcnow().isoformat())}"
                        }
                    ]
                }
            ]
        }


class EmailNotifier(Notifier):
    """
    Email notification channel.
    
    Sends HTML emails via SMTP.
    """
    
    def __init__(self, smtp_config: dict):
        """
        Initialize email notifier.
        
        Args:
            smtp_config: SMTP configuration dict
        """
        self.smtp_config = smtp_config
    
    async def send(self, message: dict) -> bool:
        """Send email notification."""
        try:
            # In production, use aiosmtplib or similar
            logger.info(f"Email notification: {message.get('title')}")
            
            # Placeholder for actual SMTP logic
            # import aiosmtplib
            # await aiosmtplib.send(...)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class AuditNotifier(Notifier):
    """
    Audit log notifier.
    
    Logs notifications to audit trail for compliance.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit notifier.
        
        Args:
            log_file: Optional audit log file path
        """
        self.log_file = log_file
        
        # Setup audit logger
        self.audit_logger = logging.getLogger("audit")
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.audit_logger.addHandler(handler)
    
    async def send(self, message: dict) -> bool:
        """Log to audit trail."""
        try:
            self.audit_logger.info(
                f"AUDIT: {message.get('title')} | "
                f"Severity: {message.get('severity')} | "
                f"Details: {message.get('description')}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            return False


class NotifierService:
    """
    Notification routing service.
    
    Manages multiple notification channels and routing rules.
    Implements Observer pattern subscribers for events.
    """
    
    def __init__(self):
        """Initialize notifier service."""
        self.notifiers: List[Notifier] = []
        
        # Initialize notifiers based on config
        if settings.slack_webhook_url:
            self.notifiers.append(SlackNotifier(settings.slack_webhook_url))
        
        if settings.email_enabled:
            self.notifiers.append(EmailNotifier({
                "host": settings.email_host,
                "port": settings.email_port,
                "username": settings.email_username,
                "password": settings.email_password
            }))
        
        # Always enable audit logging
        self.notifiers.append(AuditNotifier())
        
        logger.info(f"Initialized {len(self.notifiers)} notifiers")
    
    async def notify(
        self,
        title: str,
        description: str,
        severity: str = "MEDIUM",
        metadata: dict = None
    ):
        """
        Send notification to all channels.
        
        Args:
            title: Notification title
            description: Notification description
            severity: Severity level
            metadata: Additional metadata
        """
        message = {
            "title": title,
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Send to all notifiers
        results = []
        for notifier in self.notifiers:
            success = await notifier.send(message)
            results.append(success)
        
        logger.info(f"Notification sent: {sum(results)}/{len(results)} successful")
    
    async def notify_security_alert(self, alert: SecurityAlert):
        """
        Send security alert notification.
        
        Args:
            alert: SecurityAlert object
        """
        await self.notify(
            title=f"🚨 Alerte Sécurité: {alert.title}",
            description=alert.description,
            severity=alert.severity.value,
            metadata={
                "rule_id": alert.rule_id,
                "user_id": alert.user_id,
                "username": alert.username,
                "recommendation": alert.recommendation
            }
        )
    
    async def handle_event(self, event: Event):
        """
        Event handler for automatic notifications.
        
        Args:
            event: Event object
        """
        if event.type == EventType.SECURITY_ALERT:
            await self.notify(
                title=f"Alerte de sécurité détectée",
                description=f"Règle: {event.data.get('rule_id')}",
                severity=event.data.get('severity', 'MEDIUM')
            )
        
        elif event.type == EventType.SAVINGS_ACHIEVED:
            await self.notify(
                title=f"💰 Économies réalisées!",
                description=f"${event.data.get('amount', 0):.2f} économisés",
                severity="LOW"
            )


# Default instance
notifier_service = NotifierService()

