# backend/app/services/document_service.py
"""
Document handling business logic.

Handles:
- Reference and retrieval of documents from OneDrive or local storage
- File metadata tracking in database
- Association of documents with payments
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, BinaryIO
from fastapi import UploadFile

from app.core.config import PATHS
from app.database.database import execute_query, execute_write_query, get_db_connection

async def get_document_path(document_id: int) -> Optional[Path]:
    """
    Get the complete file system path for a document.
    
    Args:
        document_id: Document ID in the database
        
    Returns: Full filesystem path to the document or None if not found
    """
    query = """
    SELECT file_name, onedrive_path
    FROM client_files
    WHERE file_id = ?
    """
    results = await execute_query(query, (document_id,))
    
    if not results:
        return None
    
    document = results[0]
    onedrive_path = document.get("onedrive_path")
    
    if not onedrive_path:
        return None
    
    # Determine if we should use OneDrive path or local path
    if PATHS["APP_MODE"] == "office":
        # Use OneDrive path for office mode
        full_path = Path(onedrive_path)
    else:
        # For home/dev mode, use local documents directory
        base_path = Path(__file__).parent.parent.parent / "documents"
        file_name = document.get("file_name", "unknown.pdf")
        full_path = base_path / str(document_id) / file_name
    
    # Check if file exists
    if not full_path.exists():
        return None
    
    return full_path

async def store_document(
    file: UploadFile,
    client_id: int,
    description: Optional[str] = None
) -> Optional[int]:
    """
    Store a document and create metadata record.
    
    Args:
        file: Uploaded file object
        client_id: Client ID
        description: Optional document description
        
    Returns: Document ID of the newly created record or None on failure
    """
    # Generate file paths
    original_filename = file.filename or "unnamed_file"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{original_filename}"
    
    # Determine the appropriate storage location
    if PATHS["APP_MODE"] == "office":
        # Get OneDrive folder path from client record
        client_query = """
        SELECT onedrive_folder_path
        FROM clients
        WHERE client_id = ?
        """
        client_results = await execute_query(client_query, (client_id,))
        
        if not client_results or not client_results[0].get("onedrive_folder_path"):
            # Fall back to a default path
            onedrive_folder = PATHS["BASE_PATH"] / "client_documents" / str(client_id)
        else:
            onedrive_folder = Path(client_results[0]["onedrive_folder_path"])
        
        # Ensure directory exists
        os.makedirs(onedrive_folder, exist_ok=True)
        
        file_path = onedrive_folder / safe_filename
        onedrive_path = str(file_path)
    else:
        # For home/dev mode, use local documents directory
        doc_dir = Path(__file__).parent.parent.parent / "documents" / str(client_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        file_path = doc_dir / safe_filename
        onedrive_path = f"documents/{client_id}/{safe_filename}"
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            # Read the file in chunks to handle large files
            contents = await file.read()
            buffer.write(contents)
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return None
    
    # Create database record
    query = """
    INSERT INTO client_files (
        client_id, file_name, onedrive_path, description, uploaded_at
    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    params = (client_id, original_filename, onedrive_path, description)
    
    try:
        async with get_db_connection() as conn:
            async with conn.execute("BEGIN") as _:
                try:
                    # Insert the file record
                    file_id = await execute_write_query(query, params)
                    
                    # Remove payment associations
                    await conn.execute(
                        "DELETE FROM payment_files WHERE file_id = ?",
                        (file_id,)
                    )
                    
                    await conn.commit()
                    return file_id
                except Exception as e:
                    await conn.rollback()
                    # If database insert fails, delete the file to prevent orphaned files
                    if file_path.exists():
                        os.remove(file_path)
                    print(f"Error creating file record: {str(e)}")
                    return None
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
        return None

async def associate_document_with_payment(file_id: int, payment_id: int) -> bool:
    """
    Create an association between a document and a payment.
    
    Args:
        file_id: Document file ID
        payment_id: Payment ID
        
    Returns: Boolean indicating success
    """
    # Check if the association already exists
    check_query = """
    SELECT 1 FROM payment_files
    WHERE file_id = ? AND payment_id = ?
    """
    existing = await execute_query(check_query, (file_id, payment_id))
    
    if existing:
        return True  # Already associated
    
    # Create the association
    query = """
    INSERT INTO payment_files (payment_id, file_id, linked_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    """
    
    try:
        async with get_db_connection() as conn:
            async with conn.execute("BEGIN") as _:
                try:
                    await execute_write_query(query, (payment_id, file_id))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"Error associating document: {str(e)}")
                    return False
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
        return False

async def get_payment_documents(payment_id: int) -> list[dict[str, Any]]:
    """
    Get documents associated with a payment.
    
    Args:
        payment_id: Payment ID
        
    Returns: List of document metadata
    """
    query = """
    SELECT 
        cf.file_id,
        cf.file_name,
        cf.onedrive_path,
        cf.description,
        cf.uploaded_at,
        pf.linked_at
    FROM 
        client_files cf
    JOIN 
        payment_files pf ON cf.file_id = pf.file_id
    WHERE 
        pf.payment_id = ?
    ORDER BY 
        pf.linked_at DESC
    """
    
    return await execute_query(query, (payment_id,))

async def delete_document(document_id: int) -> bool:
    """
    Delete a document and its file.
    
    Args:
        document_id: Document ID
        
    Returns: Boolean indicating success
    """
    # First, get the document details
    document_path = await get_document_path(document_id)
    
    if not document_path:
        return False  # Document not found
    
    async with get_db_connection() as conn:
        async with conn.execute("BEGIN") as _:
            try:
                # Remove payment associations
                await conn.execute(
                    "DELETE FROM payment_files WHERE file_id = ?",
                    (document_id,)
                )
                
                # Delete the database record
                await conn.execute(
                    "DELETE FROM client_files WHERE file_id = ?",
                    (document_id,)
                )
                
                # Delete the physical file
                if document_path.exists():
                    os.remove(document_path)
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                print(f"Error deleting document: {str(e)}")
                return False