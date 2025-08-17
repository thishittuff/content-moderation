from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import ContentType, ModerationStatus, ContentClassification, NotificationChannel


# Request Schemas
class TextModerationRequest(BaseModel):
    email_id: EmailStr = Field(..., description="User's email address")
    text_content: str = Field(..., min_length=1, max_length=10000, description="Text content to moderate")


class ImageModerationRequest(BaseModel):
    email_id: EmailStr = Field(..., description="User's email address")
    image_data: str = Field(..., description="Base64 encoded image data")


class AnalyticsRequest(BaseModel):
    user: EmailStr = Field(..., description="User's email address for analytics")


# Response Schemas
class ModerationResultResponse(BaseModel):
    id: int
    classification: ContentClassification
    confidence: float
    reasoning: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModerationRequestResponse(BaseModel):
    id: int
    email_id: str
    content_type: ContentType
    status: ModerationStatus
    created_at: datetime
    result: Optional[ModerationResultResponse] = None
    
    class Config:
        from_attributes = True


class NotificationLogResponse(BaseModel):
    id: int
    channel: NotificationChannel
    status: str
    sent_at: datetime
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class AnalyticsSummaryResponse(BaseModel):
    user_email: str
    total_requests: int
    safe_content: int
    inappropriate_content: int
    pending_requests: int
    recent_requests: List[ModerationRequestResponse]
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
