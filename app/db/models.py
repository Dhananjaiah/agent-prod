"""SQLAlchemy database models for the insurance system."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Customer(Base):
    """Customer entity - represents insurance policyholders."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    policies: Mapped[list["Policy"]] = relationship(
        "Policy", back_populates="customer", lazy="selectin"
    )

    __table_args__ = (Index("ix_customers_email", "email"),)


class Policy(Base):
    """Insurance policy entity."""

    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    policy_type: Mapped[str] = mapped_column(
        Enum("auto", "home", "life", "health", "travel", name="policy_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "expired", "cancelled", "pending", name="policy_status_enum"),
        default="active",
        nullable=False,
    )
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deductible: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="policies")
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="policy", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="policy",
        foreign_keys="Document.policy_id",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_policies_policy_number", "policy_number"),
        Index("ix_policies_customer_id", "customer_id"),
    )


class Claim(Base):
    """Insurance claim entity."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "submitted",
            "under_review",
            "approved",
            "denied",
            "paid",
            "closed",
            name="claim_status_enum",
        ),
        default="submitted",
        nullable=False,
    )
    claim_type: Mapped[str] = mapped_column(
        Enum(
            "accident",
            "theft",
            "damage",
            "medical",
            "liability",
            "natural_disaster",
            name="claim_type_enum",
        ),
        nullable=False,
    )
    claim_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    incident_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    filed_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="claims")
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="claim",
        foreign_keys="Document.claim_id",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_claims_claim_number", "claim_number"),
        Index("ix_claims_policy_id", "policy_id"),
        Index("ix_claims_status", "status"),
    )


class Document(Base):
    """Document metadata entity (S3/SharePoint style storage)."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(
        Enum(
            "policy_document",
            "claim_form",
            "evidence",
            "invoice",
            "correspondence",
            "id_proof",
            "medical_report",
            name="document_type_enum",
        ),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_provider: Mapped[str] = mapped_column(
        Enum("s3", "sharepoint", "local", name="storage_provider_enum"),
        default="s3",
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id")
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id")
    )
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(255))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    policy: Mapped[Optional["Policy"]] = relationship(
        "Policy", back_populates="documents", foreign_keys=[policy_id]
    )
    claim: Mapped[Optional["Claim"]] = relationship(
        "Claim", back_populates="documents", foreign_keys=[claim_id]
    )

    __table_args__ = (
        Index("ix_documents_policy_id", "policy_id"),
        Index("ix_documents_claim_id", "claim_id"),
        Index("ix_documents_document_type", "document_type"),
    )
