import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.models import NotificationChannel, ModerationRequest, ModerationResult
import httpx
import json

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.slack_token = settings.slack_bot_token
        self.slack_channel = settings.slack_channel_id
        self.brevo_api_key = settings.brevo_api_key
        self.sender_email = settings.brevo_sender_email
    
    async def send_slack_notification(self, request: ModerationRequest, result: ModerationResult) -> Dict[str, Any]:
        """Send Slack notification for inappropriate content"""
        if not self.slack_token or not self.slack_channel:
            logger.warning("Slack configuration not available")
            return {"status": "failed", "error": "Slack not configured"}
        
        try:
            # Determine if notification is needed
            if result.classification.value == "safe":
                return {"status": "skipped", "reason": "Content is safe"}
            
            # Create Slack message
            color = self._get_slack_color(result.classification.value)
            message = {
                "channel": self.slack_channel,
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 Content Moderation Alert - {result.classification.value.upper()}",
                        "fields": [
                            {
                                "title": "User Email",
                                "value": request.email_id,
                                "short": True
                            },
                            {
                                "title": "Content Type",
                                "value": request.content_type.value,
                                "short": True
                            },
                            {
                                "title": "Classification",
                                "value": result.classification.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Confidence",
                                "value": f"{result.confidence:.2f}",
                                "short": True
                            },
                            {
                                "title": "Reasoning",
                                "value": result.reasoning or "No reasoning provided",
                                "short": False
                            },
                            {
                                "title": "Request ID",
                                "value": str(request.id),
                                "short": True
                            }
                        ],
                        "footer": "Content Moderation Service",
                        "ts": int(request.created_at.timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={
                        "Authorization": f"Bearer {self.slack_token}",
                        "Content-Type": "application/json"
                    },
                    json=message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    slack_response = response.json()
                    if slack_response.get("ok"):
                        logger.info(f"Slack notification sent successfully for request {request.id}")
                        return {"status": "sent", "slack_response": slack_response}
                    else:
                        logger.error(f"Slack API error: {slack_response}")
                        return {"status": "failed", "error": slack_response.get("error", "Unknown error")}
                else:
                    logger.error(f"Slack API HTTP error: {response.status_code}")
                    return {"status": "failed", "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def send_email_notification(self, request: ModerationRequest, result: ModerationResult) -> Dict[str, Any]:
        """Send email notification for inappropriate content using BrevoMail API"""
        if not self.brevo_api_key or not self.sender_email:
            logger.warning("BrevoMail configuration not available")
            return {"status": "failed", "error": "BrevoMail not configured"}
        
        try:
            # Determine if notification is needed
            if result.classification.value == "safe":
                return {"status": "skipped", "reason": "Content is safe"}
            
            # Create email content
            subject = f"Content Moderation Alert - {result.classification.value.upper()}"
            
            html_content = f"""
            <html>
            <body>
                <h2>🚨 Content Moderation Alert</h2>
                <p><strong>Classification:</strong> {result.classification.value.upper()}</p>
                <p><strong>User Email:</strong> {request.email_id}</p>
                <p><strong>Content Type:</strong> {request.content_type.value}</p>
                <p><strong>Confidence:</strong> {result.confidence:.2f}</p>
                <p><strong>Reasoning:</strong> {result.reasoning or 'No reasoning provided'}</p>
                <p><strong>Request ID:</strong> {request.id}</p>
                <p><strong>Timestamp:</strong> {request.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <hr>
                <p><em>This is an automated alert from the Content Moderation Service.</em></p>
            </body>
            </html>
            """
            
            # Send via BrevoMail API
            email_data = {
                "sender": {
                    "name": "Content Moderation Service",
                    "email": self.sender_email
                },
                "to": [
                    {
                        "email": request.email_id,
                        "name": "User"
                    }
                ],
                "subject": subject,
                "htmlContent": html_content
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.brevo.com/v3/sendTransacEmail",
                    headers={
                        "api-key": self.brevo_api_key,
                        "Content-Type": "application/json"
                    },
                    json=email_data,
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    logger.info(f"Email notification sent successfully for request {request.id}")
                    return {"status": "sent", "email_response": response.json()}
                else:
                    logger.error(f"BrevoMail API error: {response.status_code} - {response.text}")
                    return {"status": "failed", "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _get_slack_color(self, classification: str) -> str:
        """Get appropriate Slack color for classification"""
        colors = {
            "safe": "good",
            "toxic": "danger",
            "spam": "warning",
            "harassment": "danger",
            "inappropriate": "warning"
        }
        return colors.get(classification, "warning")
    
    async def send_notifications(self, request: ModerationRequest, result: ModerationResult) -> Dict[str, Any]:
        """Send notifications through all configured channels"""
        notifications = {}
        
        # Send Slack notification
        if self.slack_token and self.slack_channel:
            notifications["slack"] = await self.send_slack_notification(request, result)
        
        # Send email notification
        if self.brevo_api_key and self.sender_email:
            notifications["email"] = await self.send_email_notification(request, result)
        
        return notifications
