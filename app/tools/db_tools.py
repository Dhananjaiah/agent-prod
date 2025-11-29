"""Database query tools for the LangChain/LangGraph agent."""
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, Customer, Document, Policy
from app.db.session import SyncSessionLocal


def _serialize_value(value: Any) -> Any:
    """Serialize values for JSON output."""
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    return value


def _model_to_dict(model: Any) -> dict[str, Any]:
    """Convert SQLAlchemy model to dictionary."""
    if model is None:
        return {}
    return {
        key: _serialize_value(getattr(model, key))
        for key in model.__table__.columns.keys()
    }


def get_customer_by_id(customer_id: str) -> str:
    """
    Get customer information by their ID.

    Args:
        customer_id: The UUID of the customer to look up.

    Returns:
        JSON string with customer information or error message.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Customer).where(Customer.id == UUID(customer_id))
            )
            customer = result.scalar_one_or_none()

            if customer:
                return json.dumps(
                    {"success": True, "data": _model_to_dict(customer)}, indent=2
                )
            return json.dumps(
                {"success": False, "error": f"Customer with ID {customer_id} not found"}
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_customer_by_email(email: str) -> str:
    """
    Get customer information by their email address.

    Args:
        email: The email address of the customer.

    Returns:
        JSON string with customer information or error message.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Customer).where(Customer.email == email)
            )
            customer = result.scalar_one_or_none()

            if customer:
                return json.dumps(
                    {"success": True, "data": _model_to_dict(customer)}, indent=2
                )
            return json.dumps(
                {"success": False, "error": f"Customer with email {email} not found"}
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_policy_by_id(policy_id: str) -> str:
    """
    Get policy information by policy ID.

    Args:
        policy_id: The UUID of the policy.

    Returns:
        JSON string with policy information including customer details.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Policy).where(Policy.id == UUID(policy_id))
            )
            policy = result.scalar_one_or_none()

            if policy:
                policy_data = _model_to_dict(policy)

                # Get customer info
                customer_result = session.execute(
                    select(Customer).where(Customer.id == policy.customer_id)
                )
                customer = customer_result.scalar_one_or_none()
                if customer:
                    policy_data["customer"] = _model_to_dict(customer)

                return json.dumps({"success": True, "data": policy_data}, indent=2)
            return json.dumps(
                {"success": False, "error": f"Policy with ID {policy_id} not found"}
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_policy_by_number(policy_number: str) -> str:
    """
    Get policy information by policy number.

    Args:
        policy_number: The policy number (e.g., 'POL-AUTO-12345').

    Returns:
        JSON string with policy information including customer details.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Policy).where(Policy.policy_number == policy_number)
            )
            policy = result.scalar_one_or_none()

            if policy:
                policy_data = _model_to_dict(policy)

                # Get customer info
                customer_result = session.execute(
                    select(Customer).where(Customer.id == policy.customer_id)
                )
                customer = customer_result.scalar_one_or_none()
                if customer:
                    policy_data["customer"] = _model_to_dict(customer)

                return json.dumps({"success": True, "data": policy_data}, indent=2)
            return json.dumps(
                {
                    "success": False,
                    "error": f"Policy with number {policy_number} not found",
                }
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_policies_by_customer_id(customer_id: str) -> str:
    """
    Get all policies for a specific customer.

    Args:
        customer_id: The UUID of the customer.

    Returns:
        JSON string with list of policies.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Policy).where(Policy.customer_id == UUID(customer_id))
            )
            policies = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(policies),
                    "data": [_model_to_dict(p) for p in policies],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_claim_by_id(claim_id: str) -> str:
    """
    Get claim information by claim ID.

    Args:
        claim_id: The UUID of the claim.

    Returns:
        JSON string with claim information including policy details.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Claim).where(Claim.id == UUID(claim_id))
            )
            claim = result.scalar_one_or_none()

            if claim:
                claim_data = _model_to_dict(claim)

                # Get policy info
                policy_result = session.execute(
                    select(Policy).where(Policy.id == claim.policy_id)
                )
                policy = policy_result.scalar_one_or_none()
                if policy:
                    claim_data["policy"] = _model_to_dict(policy)

                return json.dumps({"success": True, "data": claim_data}, indent=2)
            return json.dumps(
                {"success": False, "error": f"Claim with ID {claim_id} not found"}
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_claim_by_number(claim_number: str) -> str:
    """
    Get claim information by claim number.

    Args:
        claim_number: The claim number (e.g., 'CLM-2024-00001').

    Returns:
        JSON string with claim information including policy details.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Claim).where(Claim.claim_number == claim_number)
            )
            claim = result.scalar_one_or_none()

            if claim:
                claim_data = _model_to_dict(claim)

                # Get policy info
                policy_result = session.execute(
                    select(Policy).where(Policy.id == claim.policy_id)
                )
                policy = policy_result.scalar_one_or_none()
                if policy:
                    claim_data["policy"] = _model_to_dict(policy)

                return json.dumps({"success": True, "data": claim_data}, indent=2)
            return json.dumps(
                {
                    "success": False,
                    "error": f"Claim with number {claim_number} not found",
                }
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_claims_by_policy_id(policy_id: str) -> str:
    """
    Get all claims for a specific policy.

    Args:
        policy_id: The UUID of the policy.

    Returns:
        JSON string with list of claims.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Claim).where(Claim.policy_id == UUID(policy_id))
            )
            claims = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(claims),
                    "data": [_model_to_dict(c) for c in claims],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_claims_by_status(status: str) -> str:
    """
    Get claims filtered by status.

    Args:
        status: The claim status (submitted, under_review, approved, denied, paid, closed).

    Returns:
        JSON string with list of claims matching the status.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Claim).where(Claim.status == status).limit(50)
            )
            claims = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(claims),
                    "data": [_model_to_dict(c) for c in claims],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_documents_for_policy(policy_id: str) -> str:
    """
    Get all documents associated with a policy.

    Args:
        policy_id: The UUID of the policy.

    Returns:
        JSON string with list of documents.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Document).where(Document.policy_id == UUID(policy_id))
            )
            documents = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(documents),
                    "data": [_model_to_dict(d) for d in documents],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def get_documents_for_claim(claim_id: str) -> str:
    """
    Get all documents associated with a claim.

    Args:
        claim_id: The UUID of the claim.

    Returns:
        JSON string with list of documents.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Document).where(Document.claim_id == UUID(claim_id))
            )
            documents = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(documents),
                    "data": [_model_to_dict(d) for d in documents],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def search_policies(query: str) -> str:
    """
    Search policies by policy number or type.

    Args:
        query: Search term to match against policy numbers or types.

    Returns:
        JSON string with list of matching policies.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Policy)
                .where(
                    Policy.policy_number.ilike(f"%{query}%")
                    | Policy.policy_type.ilike(f"%{query}%")
                )
                .limit(20)
            )
            policies = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(policies),
                    "data": [_model_to_dict(p) for p in policies],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def search_claims(query: str) -> str:
    """
    Search claims by claim number or type.

    Args:
        query: Search term to match against claim numbers or types.

    Returns:
        JSON string with list of matching claims.
    """
    try:
        with SyncSessionLocal() as session:
            result = session.execute(
                select(Claim)
                .where(
                    Claim.claim_number.ilike(f"%{query}%")
                    | Claim.claim_type.ilike(f"%{query}%")
                )
                .limit(20)
            )
            claims = result.scalars().all()

            return json.dumps(
                {
                    "success": True,
                    "count": len(claims),
                    "data": [_model_to_dict(c) for c in claims],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
