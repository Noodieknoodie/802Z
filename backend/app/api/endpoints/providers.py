# backend/app/api/endpoints/providers.py
"""
Provider API endpoints.

Provides routes for:
- Listing all providers
- Getting clients by provider
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Any

from app.database.models import get_providers, get_provider_clients

router = APIRouter(
    prefix="/api/providers",
    tags=["providers"],
)

@router.get("")
async def get_all_providers():
    """
    GET /api/providers
    
    Returns: JSON response with array of provider objects including aggregated stats
    """
    providers = await get_providers()
    return {"providers": providers}

@router.get("/{provider_id}/clients")
async def get_provider_clients_endpoint(
    provider_id: int = Path(..., description="The provider ID")
):
    """
    GET /api/providers/{provider_id}/clients
    
    Returns: JSON response with array of client objects belonging to the provider
    """
    clients = await get_provider_clients(provider_id)
    
    if not clients and provider_id > 0:
        # Check if provider exists
        providers = await get_providers()
        provider_exists = any(p.get("id") == provider_id for p in providers)
        
        if not provider_exists:
            raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"clients": clients}