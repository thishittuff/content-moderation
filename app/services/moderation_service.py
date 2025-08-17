import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import (
    ModerationRequest, ModerationResult, NotificationLog,
    ContentType, ModerationStatus, ContentClassification, NotificationChannel
)
from app.services.gemini_service import GeminiService
from app.services.notification_service import NotificationService
from app.services.sentry_service import SentryService
from app.schemas import TextModerationRequest, ImageModerationRequest
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class ModerationService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.notification_service = NotificationService()
        self.sentry_service = SentryService()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def moderate_text_content(
        self, 
        db: AsyncSession, 
        request_data: TextModerationRequest
    ) -> Dict[str, Any]:
        """Moderate text content using AI analysis"""
        try:
            # Generate content hash
            content_hash = self._generate_content_hash(request_data.text_content)
            
            # Check for duplicate content
            existing_request = await self._get_existing_request(db, content_hash)
            if existing_request:
                logger.info(f"Duplicate content detected for hash: {content_hash}")
                return await self._get_moderation_result(db, existing_request.id)
            
            # Create moderation request
            moderation_request = ModerationRequest(
                email_id=request_data.email_id,
                content_type=ContentType.TEXT,
                content_hash=content_hash,
                status=ModerationStatus.PROCESSING
            )
            
            db.add(moderation_request)
            await db.commit()
            await db.refresh(moderation_request)
            
            logger.info(f"Created moderation request {moderation_request.id} for text content")
            
            # Analyze content using Gemini
            classification, confidence, reasoning, llm_response = await self.gemini_service.analyze_text_content(
                request_data.text_content
            )
            
            # Create moderation result
            moderation_result = ModerationResult(
                request_id=moderation_request.id,
                classification=classification,
                confidence=confidence,
                reasoning=reasoning,
                llm_response=llm_response
            )
            
            db.add(moderation_result)
            
            # Update request status
            moderation_request.status = ModerationStatus.COMPLETED
            
            await db.commit()
            await db.refresh(moderation_request)
            await db.refresh(moderation_result)
            
            logger.info(f"Text moderation completed for request {moderation_request.id}")
            
            # Send notifications if content is inappropriate
            if classification != ContentClassification.SAFE:
                await self._send_notifications(moderation_request, moderation_result, db)
            
            return await self._get_moderation_result(db, moderation_request.id)
            
        except Exception as e:
            logger.error(f"Error in text moderation: {e}")
            await self._handle_moderation_error(db, e, request_data.email_id, ContentType.TEXT)
            raise
    
    async def moderate_image_content(
        self, 
        db: AsyncSession, 
        request_data: ImageModerationRequest
    ) -> Dict[str, Any]:
        """Moderate image content using AI analysis"""
        try:
            # Generate content hash
            content_hash = self._generate_content_hash(request_data.image_data)
            
            # Check for duplicate content
            existing_request = await self._get_existing_request(db, content_hash)
            if existing_request:
                logger.info(f"Duplicate image detected for hash: {content_hash}")
                return await self._get_moderation_result(db, existing_request.id)
            
            # Create moderation request
            moderation_request = ModerationRequest(
                email_id=request_data.email_id,
                content_type=ContentType.IMAGE,
                content_hash=content_hash,
                status=ModerationStatus.PROCESSING
            )
            
            db.add(moderation_request)
            await db.commit()
            await db.refresh(moderation_request)
            
            logger.info(f"Created moderation request {moderation_request.id} for image content")
            
            # Analyze content using Gemini Vision
            classification, confidence, reasoning, llm_response = await self.gemini_service.analyze_image_content(
                request_data.image_data
            )
            
            # Create moderation result
            moderation_result = ModerationResult(
                request_id=moderation_request.id,
                classification=classification,
                confidence=confidence,
                reasoning=reasoning,
                llm_response=llm_response
            )
            
            db.add(moderation_result)
            
            # Update request status
            moderation_request.status = ModerationStatus.COMPLETED
            
            await db.commit()
            await db.refresh(moderation_request)
            await db.refresh(moderation_result)
            
            logger.info(f"Image moderation completed for request {moderation_request.id}")
            
            # Send notifications if content is inappropriate
            if classification != ContentClassification.SAFE:
                await self._send_notifications(moderation_request, moderation_result, db)
            
            return await self._get_moderation_result(db, moderation_request.id)
            
        except Exception as e:
            logger.error(f"Error in image moderation: {e}")
            await self._handle_moderation_error(db, e, request_data.email_id, ContentType.IMAGE)
            raise
    
    async def get_user_analytics(
        self, 
        db: AsyncSession, 
        user_email: str
    ) -> Dict[str, Any]:
        """Get analytics summary for a specific user"""
        try:
            # Get total requests
            total_requests = await db.scalar(
                select(func.count(ModerationRequest.id))
                .where(ModerationRequest.email_id == user_email)
            ) or 0
            
            # Get safe content count
            safe_content = await db.scalar(
                select(func.count(ModerationResult.id))
                .join(ModerationRequest)
                .where(
                    ModerationRequest.email_id == user_email,
                    ModerationResult.classification == ContentClassification.SAFE
                )
            ) or 0
            
            # Get inappropriate content count
            inappropriate_content = await db.scalar(
                select(func.count(ModerationResult.id))
                .join(ModerationRequest)
                .where(
                    ModerationRequest.email_id == user_email,
                    ModerationResult.classification != ContentClassification.SAFE
                )
            ) or 0
            
            # Get pending requests count
            pending_requests = await db.scalar(
                select(func.count(ModerationRequest.id))
                .where(
                    ModerationRequest.email_id == user_email,
                    ModerationRequest.status == ModerationStatus.PENDING
                )
            ) or 0
            
            # Get recent requests with eager loading
            recent_result = await db.execute(
                select(ModerationRequest)
                .options(selectinload(ModerationRequest.result))
                .where(ModerationRequest.email_id == user_email)
                .order_by(ModerationRequest.created_at.desc())
                .limit(10)
            )
            
            recent_requests_raw = recent_result.scalars().all()
            
            # Convert to serializable format
            recent_requests = []
            for req in recent_requests_raw:
                result_data = None
                if req.result:
                    result_data = {
                        "id": req.result.id,
                        "classification": req.result.classification.value,
                        "confidence": req.result.confidence,
                        "reasoning": req.result.reasoning,
                        "created_at": req.result.created_at.isoformat()
                    }
                
                recent_requests.append({
                    "id": req.id,
                    "email_id": req.email_id,
                    "content_type": req.content_type.value,
                    "status": req.status.value,
                    "created_at": req.created_at.isoformat(),
                    "result": result_data
                })
            
            return {
                "user_email": user_email,
                "total_requests": total_requests,
                "safe_content": safe_content,
                "inappropriate_content": inappropriate_content,
                "pending_requests": pending_requests,
                "recent_requests": recent_requests
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            await self._handle_analytics_error(e, user_email)
            raise
    
    async def _get_existing_request(self, db: AsyncSession, content_hash: str) -> Optional[ModerationRequest]:
        """Get existing moderation request by content hash"""
        result = await db.execute(
            select(ModerationRequest)
            .where(ModerationRequest.content_hash == content_hash)
        )
        return result.scalar_one_or_none()
    
    async def _get_moderation_result(self, db: AsyncSession, request_id: int) -> Dict[str, Any]:
        """Get complete moderation result including request and result data"""
        result = await db.execute(
            select(ModerationRequest)
            .options(selectinload(ModerationRequest.result))
            .where(ModerationRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise ValueError(f"Moderation request {request_id} not found")
        
        # Convert result to serializable format
        result_data = None
        if request.result:
            result_data = {
                "id": request.result.id,
                "classification": request.result.classification.value,
                "confidence": request.result.confidence,
                "reasoning": request.result.reasoning,
                "created_at": request.result.created_at.isoformat()
            }
        
        return {
            "id": request.id,
            "email_id": request.email_id,
            "content_type": request.content_type.value,
            "status": request.status.value,
            "created_at": request.created_at.isoformat(),
            "result": result_data
        }
    
    async def _send_notifications(
        self, 
        request: ModerationRequest, 
        result: ModerationResult, 
        db: AsyncSession
    ):
        """Send notifications for inappropriate content"""
        try:
            # Send notifications
            notification_results = await self.notification_service.send_notifications(request, result)
            
            # Log notification attempts
            for channel, result_data in notification_results.items():
                notification_log = NotificationLog(
                    request_id=request.id,
                    channel=NotificationChannel(channel),
                    status=result_data.get("status", "failed"),
                    error_message=result_data.get("error")
                )
                db.add(notification_log)
            
            await db.commit()
            logger.info(f"Notifications sent for request {request.id}")
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            # Don't fail the main request if notifications fail
    
    async def _handle_moderation_error(
        self, 
        db: AsyncSession, 
        error: Exception, 
        user_email: str, 
        content_type: ContentType
    ):
        """Handle errors during moderation and create GitHub issues"""
        try:
            # Create error context
            error_context = {
                "user_email": user_email,
                "content_type": content_type.value,
                "operation": "moderation"
            }
            
            # Handle error with Sentry service
            await self.sentry_service.handle_sentry_error(error, error_context)
            
        except Exception as sentry_error:
            logger.error(f"Failed to handle error with Sentry: {sentry_error}")
    
    async def _handle_analytics_error(self, error: Exception, user_email: str):
        """Handle errors during analytics retrieval"""
        try:
            # Create error context
            error_context = {
                "user_email": user_email,
                "operation": "analytics"
            }
            
            # Handle error with Sentry service
            await self.sentry_service.handle_sentry_error(error, error_context)
            
        except Exception as sentry_error:
            logger.error(f"Failed to handle analytics error with Sentry: {sentry_error}")