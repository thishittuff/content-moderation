from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.moderation_service import ModerationService
from app.schemas import (
    TextModerationRequest, ImageModerationRequest, AnalyticsRequest,
    ModerationRequestResponse, AnalyticsSummaryResponse, ErrorResponse, SuccessResponse
)
from app.services.sentry_service import SentryService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
moderation_service = ModerationService()
sentry_service = SentryService()


@router.post("/moderate/text", response_model=ModerationRequestResponse)
async def moderate_text(
    request: TextModerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Moderate text content using AI analysis
    
    - **email_id**: User's email address
    - **text_content**: Text content to moderate (1-10000 characters)
    """
    try:
        logger.info(f"Text moderation request - User: {request.email_id}")
        
        result = await moderation_service.moderate_text_content(db, request)
        
        logger.info(f"Text moderation completed - User: {request.email_id}")
        return result
        
    except Exception as e:
        logger.error(f"Text moderation failed: {e}")
        
        # Handle error with Sentry and create GitHub issue
        background_tasks.add_task(
            sentry_service.handle_sentry_error,
            e,
            {"user_email": request.email_id, "content_type": "text", "operation": "text_moderation"}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Text moderation failed: {str(e)}"
        )


@router.post("/moderate/image", response_model=ModerationRequestResponse)
async def moderate_image(
    request: ImageModerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Moderate image content using AI analysis
    
    - **email_id**: User's email address
    - **image_data**: Base64 encoded image data
    """
    try:
        logger.info(f"Image moderation request - User: {request.email_id}")
        
        result = await moderation_service.moderate_image_content(db, request)
        
        logger.info(f"Image moderation completed - User: {request.email_id}")
        return result
        
    except Exception as e:
        logger.error(f"Image moderation failed: {e}")
        
        # Handle error with Sentry and create GitHub issue
        background_tasks.add_task(
            sentry_service.handle_sentry_error,
            e,
            {"user_email": request.email_id, "content_type": "image", "operation": "image_moderation"}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Image moderation failed: {str(e)}"
        )


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_user_analytics(
    user: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics summary for a specific user
    
    - **user**: User's email address (query parameter)
    """
    try:
        logger.info(f"Analytics request received for user: {user}")
        
        # Validate email format
        if "@" not in user or "." not in user:
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        result = await moderation_service.get_user_analytics(db, user)
        
        logger.info(f"Analytics retrieved successfully for user: {user}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        
        # Handle error with Sentry and create GitHub issue
        background_tasks.add_task(
            sentry_service.handle_sentry_error,
            e,
            {"user_email": user, "operation": "analytics"}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Analytics retrieval failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "content-moderation-service"}


@router.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Content Moderation Service",
        "version": "1.0.0",
        "description": "AI-powered content moderation service with OpenAI integration",
        "endpoints": {
            "text_moderation": "/api/v1/moderate/text",
            "image_moderation": "/api/v1/moderate/image",
            "analytics": "/api/v1/analytics/summary",
            "health": "/api/v1/health"
        }
    }
