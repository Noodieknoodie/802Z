# backend/app/api/endpoints/clients.py
"""
Client API endpoints.

Provides routes for:
- Listing all clients
- Getting client details
- Getting client payment history
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Any

from app.api.dependencies import get_db, pagination_params
from app.database.models import (
    get_all_clients,
    get_client_details,
    get_client_payment_history
)
from app.services.client_service import get_frontend_client_data

router = APIRouter(
    prefix="/api/clients",
    tags=["clients"],
)

@router.get("")
async def get_clients():
    """
    GET /api/clients
    
    Returns: JSON response with array of client objects
    """
    clients = await get_all_clients()
    return {"clients": clients}

@router.get("/data")
async def get_frontend_data():
    """
    GET /api/clients/data
    
    Returns: Complete frontend data structure
    """
    return await get_frontend_client_data()

@router.get("/{client_id}")
async def get_client(
    client_id: int = Path(..., description="The client ID")
):
    """
    GET /api/clients/{client_id}
    
    Returns: JSON response with detailed client object
    """
    client = await get_client_details(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client

@router.get("/{client_id}/payments")
async def get_client_payments(
    client_id: int = Path(..., description="The client ID"),
    pagination: dict[str, int] = Depends(pagination_params)
):
    """
    GET /api/clients/{client_id}/payments
    
    Returns: JSON response with array of payment objects and pagination metadata
    """
    payment_history = await get_client_payment_history(
        client_id, 
        page=pagination["page"], 
        page_size=pagination["page_size"]
    )
    
    return payment_history