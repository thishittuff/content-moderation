import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SentryService:
    def __init__(self):
        self.github_token = settings.github_token
        self.github_repo = settings.github_repo
        self.sentry_dsn = settings.sentry_dsn
    
    async def create_github_issue(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue for Sentry errors"""
        if not self.github_token or not self.github_repo:
            logger.warning("GitHub configuration not available")
            return {"status": "failed", "error": "GitHub not configured"}
        
        try:
            # Parse repository owner and name
            if "/" not in self.github_repo:
                return {"status": "failed", "error": "Invalid repository format. Use 'owner/repo'"}
            
            owner, repo = self.github_repo.split("/", 1)
            
            # Create issue title and body
            title = f"🚨 Sentry Error: {error_info.get('error_type', 'Unknown Error')}"
            
            body = f"""
## Sentry Error Report

**Error Type:** {error_info.get('error_type', 'Unknown')}
**Error Message:** {error_info.get('error_message', 'No message')}
**Timestamp:** {error_info.get('timestamp', datetime.now(timezone.utc).isoformat())}
**Environment:** {error_info.get('environment', 'Unknown')}

### Stack Trace
```
{error_info.get('stack_trace', 'No stack trace available')}
```

### Additional Context
- **User Email:** {error_info.get('user_email', 'N/A')}
- **Request ID:** {error_info.get('request_id', 'N/A')}
- **Content Type:** {error_info.get('content_type', 'N/A')}
- **Sentry Event ID:** {error_info.get('sentry_event_id', 'N/A')}

### Action Required
Please investigate this error and take appropriate action.

---
*This issue was automatically created by the Content Moderation Service.*
            """
            
            # Create GitHub issue
            issue_data = {
                "title": title,
                "body": body,
                "labels": ["bug", "sentry", "content-moderation"],
                "assignees": [],  # Can be configured to assign to specific team members
                "milestone": None
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/issues",
                    headers={
                        "Authorization": f"token {self.github_token}",
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "Content-Moderation-Service"
                    },
                    json=issue_data,
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    issue_response = response.json()
                    logger.info(f"GitHub issue created successfully: {issue_response.get('html_url')}")
                    return {
                        "status": "created",
                        "issue_url": issue_response.get('html_url'),
                        "issue_number": issue_response.get('number'),
                        "github_response": issue_response
                    }
                else:
                    logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                    return {"status": "failed", "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return {"status": "failed", "error": str(e)}
    
    def capture_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Capture exception and prepare data for GitHub issue creation"""
        try:
            # Extract error information
            error_info = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.sentry_environment,
                "stack_trace": self._get_stack_trace(exc),
                "sentry_event_id": self._generate_event_id(),
                **(context or {})
            }
            
            # Log the error
            logger.error(f"Exception captured: {error_info['error_type']}: {error_info['error_message']}")
            
            # Return error info for GitHub issue creation
            return error_info
            
        except Exception as e:
            logger.error(f"Failed to capture exception: {e}")
            return {
                "error_type": "ExceptionCaptureError",
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": "unknown"
            }
    
    def _get_stack_trace(self, exc: Exception) -> str:
        """Extract stack trace from exception"""
        try:
            import traceback
            return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        except:
            return "Stack trace unavailable"
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def handle_sentry_error(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle Sentry error and create GitHub issue"""
        # Capture exception information
        error_info = self.capture_exception(exc, context)
        
        # Create GitHub issue
        issue_result = await self.create_github_issue(error_info)
        
        return {
            "error_info": error_info,
            "github_issue": issue_result
        }
