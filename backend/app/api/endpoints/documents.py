# backend/app/api/endpoints/documents.py
"""
Document API endpoints.

Provides routes for:
- Uploading payment documents
- Retrieving payment documents
- Deleting payment documents
"""

def upload_document(payment_id):
    """
    POST /api/payments/{payment_id}/documents
    
    Algorithm:
    1. Validate payment_id parameter
    2. Extract document file from request (multipart/form-data)
    3. Get client_id from payment record
    4. Call services.document_service.store_document(file, client_id)
    5. Call services.document_service.associate_document_with_payment(file_id, payment_id)
    
    This endpoint handles document uploads from the payment form
    and associates them with the specified payment.
    
    Returns: JSON response with document metadata
    """
    pass

def get_document(document_id):
    """
    GET /api/documents/{document_id}
    
    Algorithm:
    1. Validate document_id parameter
    2. Call services.document_service.get_document_path(document_id)
    3. Verify file exists and get metadata
    4. Return file as streaming response with appropriate content type
    
    This endpoint serves document files for the document viewer
    when users click the document icon in payment history.
    
    Returns: File stream response with appropriate content-type header
    """
    pass

def delete_document(document_id):
    """
    DELETE /api/documents/{document_id}
    
    Algorithm:
    1. Validate document_id parameter
    2. Remove payment-document association in payment_files table
    3. If document is no longer associated with any payments, delete from client_files
    4. Delete physical file if no longer referenced
    
    This endpoint handles document deletion requests from the
    document management interface.
    
    Returns: JSON response confirming deletion
    """
    pass