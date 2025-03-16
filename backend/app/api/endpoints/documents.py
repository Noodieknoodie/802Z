# backend/app/api/endpoints/documents.py
"""
Document API endpoints.

Provides routes for:
- Uploading payment documents
- Retrieving payment documents
- Deleting payment documents
"""
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Any, Optional
import io

from app.services.document_service import (
    store_document,
    associate_document_with_payment,
    get_document_path,
    delete_document,
    get_payment_documents
)
from app.database.models import get_payment

router = APIRouter(tags=["documents"])

@router.post("/api/payments/{payment_id}/documents")
async def upload_document_for_payment(
    payment_id: int = Path(..., description="The payment ID"),
    document: UploadFile = File(..., description="Document file to upload"),
    description: Optional[str] = None
):
    """
    Upload a document and associate it with a payment.
    
    Args:
        payment_id: Payment ID
        document: Document file
        description: Optional document description
        
    Returns: Document metadata
    """
    # Check if payment exists
    payment = await get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Extract client_id from payment
    client_id = payment.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Payment has no associated client")
    
    # Store document
    document_id = await store_document(document, client_id, description)
    
    if not document_id:
        raise HTTPException(status_code=500, detail="Failed to store document")
    
    # Associate with payment
    success = await associate_document_with_payment(document_id, payment_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to associate document with payment")
    
    return {
        "id": document_id,
        "payment_id": payment_id,
        "client_id": client_id,
        "filename": document.filename,
        "success": True
    }

@router.get("/api/documents/{document_id}")
async def get_document(
    document_id: int = Path(..., description="The document ID")
):
    """
    Get a document file.
    
    Args:
        document_id: Document ID
        
    Returns: Document file as streaming response
    """
    # Get document path
    document_path = await get_document_path(document_id)
    
    if not document_path:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Read file content
    try:
        with open(document_path, "rb") as f:
            file_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")
    
    # Determine content type
    content_type = "application/octet-stream"
    extension = document_path.suffix.lower()
    
    if extension == ".pdf":
        content_type = "application/pdf"
    elif extension in [".jpg", ".jpeg"]:
        content_type = "image/jpeg"
    elif extension == ".png":
        content_type = "image/png"
    elif extension == ".txt":
        content_type = "text/plain"
    
    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={document_path.name}"}
    )

@router.delete("/api/documents/{document_id}")
async def delete_document_endpoint(
    document_id: int = Path(..., description="The document ID")
):
    """
    Delete a document and its associations.
    
    Args:
        document_id: Document ID
        
    Returns: Success message
    """
    # Delete document
    success = await delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    return {
        "success": True,
        "message": f"Document {document_id} deleted successfully"
    }

@router.get("/api/payments/{payment_id}/documents")
async def get_documents_for_payment(
    payment_id: int = Path(..., description="The payment ID")
):
    """
    Get all documents associated with a payment.
    
    Args:
        payment_id: Payment ID
        
    Returns: List of document metadata
    """
    # Check if payment exists
    payment = await get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get documents
    documents = await get_payment_documents(payment_id)
    
    return {
        "payment_id": payment_id,
        "documents": documents
    }