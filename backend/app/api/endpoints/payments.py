# backend/app/api/endpoints/payments.py
"""
Payment API endpoints.

Provides routes for:
- Getting payment history
- Creating new payments
- Updating existing payments
- Deleting payments
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body, UploadFile, File, Form
from typing import Any, Optional

from app.api.dependencies import get_db, pagination_params
from app.database.models import (
    get_client_payment_history,
    create_payment,
    update_payment,
    delete_payment,
    get_payment
)
from app.services.payment_service import (
    prepare_payment_data,
    validate_payment_data
)
from app.services.document_service import (
    store_document,
    associate_document_with_payment,
    get_payment_documents
)

router = APIRouter(tags=["payments"])

@router.post("/api/clients/{client_id}/payments")
async def create_new_payment(
    client_id: int = Path(..., description="The client ID"),
    payment_data: dict[str, Any] = Body(..., description="Payment data")
):
    """
    Create a new payment for a client.
    
    Args:
        client_id: Client ID
        payment_data: Payment data
        
    Returns: Created payment ID and data
    """
    # Add client_id to payment data
    payment_data["client_id"] = client_id
    
    # Validate payment data
    is_valid, error_message = await validate_payment_data(payment_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Prepare payment data for database
    try:
        prepared_data = await prepare_payment_data(payment_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create payment in database
    payment_id = await create_payment(prepared_data)
    
    if not payment_id:
        raise HTTPException(status_code=500, detail="Failed to create payment")
    
    # Get the created payment
    created_payment = await get_payment(payment_id)
    
    return {
        "id": payment_id,
        "payment": created_payment
    }

@router.post("/api/clients/{client_id}/payments/with-document")
async def create_payment_with_document(
    client_id: int = Path(..., description="The client ID"),
    payment_data: str = Form(..., description="Payment data as JSON string"),
    document: Optional[UploadFile] = File(None, description="Payment document")
):
    """
    Create a new payment with an attached document.
    
    Args:
        client_id: Client ID
        payment_data: Payment data as JSON string
        document: Optional document file
        
    Returns: Created payment ID with document info
    """
    import json
    
    # Parse payment data from form
    try:
        payment_dict = json.loads(payment_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in payment_data")
    
    # Add client_id to payment data
    payment_dict["client_id"] = client_id
    
    # Validate payment data
    is_valid, error_message = await validate_payment_data(payment_dict)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Prepare payment data for database
    try:
        prepared_data = await prepare_payment_data(payment_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create payment in database
    payment_id = await create_payment(prepared_data)
    
    if not payment_id:
        raise HTTPException(status_code=500, detail="Failed to create payment")
    
    # Handle document if provided
    document_id = None
    if document:
        # Store document
        document_id = await store_document(document, client_id)
        
        if document_id:
            # Associate with payment
            await associate_document_with_payment(document_id, payment_id)
    
    # Get the created payment
    created_payment = await get_payment(payment_id)
    
    return {
        "id": payment_id,
        "payment": created_payment,
        "document_id": document_id
    }

@router.put("/api/payments/{payment_id}")
async def update_existing_payment(
    payment_id: int = Path(..., description="The payment ID"),
    payment_data: dict[str, Any] = Body(..., description="Updated payment data")
):
    """
    Update an existing payment.
    
    Args:
        payment_id: Payment ID
        payment_data: Updated payment data
        
    Returns: Updated payment data
    """
    # Check if payment exists
    existing_payment = await get_payment(payment_id)
    if not existing_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Validate payment data
    is_valid, error_message = await validate_payment_data(payment_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Prepare payment data for update
    try:
        client_id = existing_payment.get("client_id")
        payment_data["client_id"] = client_id
        prepared_data = await prepare_payment_data(payment_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update payment in database
    updated_payment_id = await update_payment(payment_id, prepared_data)
    
    if not updated_payment_id:
        raise HTTPException(status_code=500, detail="Failed to update payment")
    
    # Get the updated payment
    updated_payment = await get_payment(updated_payment_id)
    
    return {
        "id": updated_payment_id,
        "payment": updated_payment
    }

@router.delete("/api/payments/{payment_id}")
async def delete_existing_payment(
    payment_id: int = Path(..., description="The payment ID")
):
    """
    Delete an existing payment.
    
    Args:
        payment_id: Payment ID
        
    Returns: Success message
    """
    # Check if payment exists
    existing_payment = await get_payment(payment_id)
    if not existing_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Delete payment from database
    success = await delete_payment(payment_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete payment")
    
    return {
        "success": True,
        "message": f"Payment {payment_id} deleted successfully"
    }

@router.get("/api/payments/{payment_id}")
async def get_payment_details(
    payment_id: int = Path(..., description="The payment ID")
):
    """
    Get details for a specific payment.
    
    Args:
        payment_id: Payment ID
        
    Returns: Payment details
    """
    # Get payment from database
    payment = await get_payment(payment_id)
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get associated documents
    documents = await get_payment_documents(payment_id)
    
    return {
        "payment": payment,
        "documents": documents
    }