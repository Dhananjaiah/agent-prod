"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True


# Customer schemas
class CustomerBase(BaseSchema):
    """Base customer schema."""

    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None


class CustomerResponse(CustomerBase):
    """Customer response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime


# Policy schemas
class PolicyBase(BaseSchema):
    """Base policy schema."""

    policy_number: str = Field(..., max_length=50)
    policy_type: str
    status: str
    premium_amount: Decimal
    coverage_amount: Decimal
    deductible: Decimal
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None


class PolicyResponse(PolicyBase):
    """Policy response schema."""

    id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime


class PolicyDetailResponse(PolicyResponse):
    """Policy response with customer details."""

    customer: Optional[CustomerResponse] = None


# Claim schemas
class ClaimBase(BaseSchema):
    """Base claim schema."""

    claim_number: str = Field(..., max_length=50)
    claim_type: str
    status: str
    claim_amount: Decimal
    approved_amount: Optional[Decimal] = None
    incident_date: datetime
    filed_date: datetime
    description: Optional[str] = None
    resolution_notes: Optional[str] = None


class ClaimResponse(ClaimBase):
    """Claim response schema."""

    id: UUID
    policy_id: UUID
    created_at: datetime
    updated_at: datetime


class ClaimDetailResponse(ClaimResponse):
    """Claim response with policy details."""

    policy: Optional[PolicyResponse] = None


# Document schemas
class DocumentBase(BaseSchema):
    """Base document schema."""

    document_name: str = Field(..., max_length=255)
    document_type: str
    storage_path: str = Field(..., max_length=500)
    storage_provider: str
    file_size_bytes: int
    mime_type: str = Field(..., max_length=100)
    is_archived: bool = False


class DocumentResponse(DocumentBase):
    """Document response schema."""

    id: UUID
    policy_id: Optional[UUID] = None
    claim_id: Optional[UUID] = None
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Chat schemas
class ChatRequest(BaseModel):
    """Chat request schema."""

    userId: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message to the agent")


class ChatResponse(BaseModel):
    """Chat response schema."""

    answer: str = Field(..., description="Agent's response to the user")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw structured data the agent used to generate the response",
    )


# Health check schema
class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    environment: str
    database: str = "connected"
