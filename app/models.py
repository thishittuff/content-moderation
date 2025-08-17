from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentClassification(str, enum.Enum):
    SAFE = "safe"
    TOXIC = "toxic"
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SLACK = "slack"


class ModerationRequest(Base):
    __tablename__ = "moderation_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String(255), nullable=False, index=True)
    content_type = Column(Enum(ContentType), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(Enum(ModerationStatus), default=ModerationStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    result = relationship("ModerationResult", back_populates="request", uselist=False)
    notifications = relationship("NotificationLog", back_populates="request")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_email_status', 'email_id', 'status'),
        Index('idx_content_hash', 'content_hash'),
    )


class ModerationResult(Base):
    __tablename__ = "moderation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("moderation_requests.id"), nullable=False)
    classification = Column(Enum(ContentClassification), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("ModerationRequest", back_populates="result")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_request_id', 'request_id'),
        Index('idx_classification', 'classification'),
    )


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("moderation_requests.id"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    status = Column(String(50), nullable=False)  # sent, failed, pending
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)
    
    # Relationships
    request = relationship("ModerationRequest", back_populates="notifications")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_request_channel', 'request_id', 'channel'),
        Index('idx_status', 'status'),
    )
