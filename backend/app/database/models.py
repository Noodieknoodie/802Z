# backend/app/database/models.py
"""
Database models and query helpers.

This module defines functions for interacting with specific database tables,
including queries, transformations, and type handling.
"""
import json
import asyncio
from typing import Any, Optional
from datetime import datetime

from app.database.database import (
    execute_query,
    execute_write_query,
    execute_transaction,
    db_connection
)
from app.services.client_service import determine_payment_status, calculate_missing_payments
from app.utils.enums import FeeType

async def get_all_clients() -> list[dict[str, Any]]:
    """
    Get all active clients from the frontend_client_list view.
    
    Returns: List of client dictionaries in frontend-expected format
    """
    query = """
    SELECT * FROM frontend_client_list
    ORDER BY name
    """
    return await execute_query(query)

async def get_client_details(client_id: int) -> dict[str, Any]:
    """
    Get detailed client information from the frontend_client_details view.
    
    Returns: Client details dictionary with all nested objects for frontend
    """
    query = """
    SELECT * FROM frontend_client_details
    WHERE id = ?
    """
    clients = await execute_query(query, (client_id,))
    
    if not clients:
        return {}
    
    client = clients[0]
    
    # Parse JSON fields if they exist as strings
    for field in ['percentRateBreakdown', 'flatRateBreakdown']:
        if field in client and isinstance(client[field], str):
            try:
                client[field] = json.loads(client[field])
            except (json.JSONDecodeError, TypeError):
                client[field] = {}
    
    # Create a unified rateBreakdown based on fee type
    if client.get('feeType') == FeeType.PERCENTAGE:
        client['rateBreakdown'] = client.get('percentRateBreakdown', {})
    else:
        client['rateBreakdown'] = client.get('flatRateBreakdown', {})
    
    # Get client payment status (replaces client_payment_status view dependency)
    client['status'] = determine_payment_status(client)
    
    # Calculate missing payments
    client['missingPayments'] = calculate_missing_payments(client)
    
    return client

async def get_client_payment_history(client_id: int, page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """
    Get payment history for a specific client from frontend_payment_history view.
    
    Returns: Dictionary with payments list and pagination metadata
    """
    # Calculate pagination parameters
    offset = (page - 1) * page_size
    
    # Get total count for pagination
    count_query = """
    SELECT COUNT(*) as total FROM frontend_payment_history
    WHERE clientId = ?
    """
    count_result = await execute_query(count_query, (client_id,))
    total = count_result[0].get('total', 0) if count_result else 0
    
    # Get paginated payment history
    query = """
    SELECT * FROM frontend_payment_history
    WHERE clientId = ?
    ORDER BY receivedDate DESC
    LIMIT ? OFFSET ?
    """
    payments = await execute_query(query, (client_id, page_size, offset))
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return {
        "payments": payments,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": total_pages,
            "hasNextPage": page < total_pages,
            "hasPreviousPage": page > 1
        }
    }

async def get_providers() -> list[dict[str, Any]]:
    """
    Get all providers with their clients and total assets.
    
    Returns: List of provider dictionaries with aggregated metrics
    """
    query = """
    SELECT 
        p.provider_id as id,
        p.name,
        COUNT(DISTINCT c.client_id) as clientCount,
        SUM(cm.last_recorded_assets) as totalAssets,
        SUM(ct.num_people) as totalParticipants
    FROM 
        providers p
    LEFT JOIN 
        contracts ct ON p.provider_id = ct.provider_id AND ct.valid_to IS NULL
    LEFT JOIN 
        clients c ON ct.client_id = c.client_id AND c.valid_to IS NULL
    LEFT JOIN 
        client_metrics cm ON c.client_id = cm.client_id
    WHERE 
        p.valid_to IS NULL
    GROUP BY 
        p.provider_id, p.name
    ORDER BY 
        p.name
    """
    return await execute_query(query)

async def get_provider_clients(provider_id: int) -> list[dict[str, Any]]:
    """
    Get all clients for a specific provider.
    
    Returns: List of client dictionaries for the specified provider
    """
    query = """
    SELECT * FROM frontend_client_list
    WHERE providerId = ?
    ORDER BY name
    """
    return await execute_query(query, (provider_id,))

async def create_payment(payment_data: dict[str, Any]) -> int:
    """
    Create a new payment record.
    
    Returns: ID of the newly created payment
    """
    query = """
    INSERT INTO payments (
        contract_id, client_id, received_date, total_assets, 
        expected_fee, actual_fee, method, notes,
        applied_start_month, applied_start_month_year, 
        applied_end_month, applied_end_month_year,
        applied_start_quarter, applied_start_quarter_year,
        applied_end_quarter, applied_end_quarter_year,
        valid_from
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    
    # Set non-applicable fields to NULL based on payment schedule
    if payment_data.get('payment_schedule') == 'monthly':
        # Zero out quarterly fields
        payment_data['applied_start_quarter'] = None
        payment_data['applied_start_quarter_year'] = None
        payment_data['applied_end_quarter'] = None
        payment_data['applied_end_quarter_year'] = None
    else:
        # Zero out monthly fields
        payment_data['applied_start_month'] = None
        payment_data['applied_start_month_year'] = None
        payment_data['applied_end_month'] = None
        payment_data['applied_end_month_year'] = None
    
    params = (
        payment_data.get('contract_id'),
        payment_data.get('client_id'),
        payment_data.get('received_date'),
        payment_data.get('total_assets'),
        payment_data.get('expected_fee'),
        payment_data.get('actual_fee'),
        payment_data.get('method'),
        payment_data.get('notes'),
        payment_data.get('applied_start_month'),
        payment_data.get('applied_start_month_year'),
        payment_data.get('applied_end_month'),
        payment_data.get('applied_end_month_year'),
        payment_data.get('applied_start_quarter'),
        payment_data.get('applied_start_quarter_year'),
        payment_data.get('applied_end_quarter'),
        payment_data.get('applied_end_quarter_year')
    )
    
    return await execute_write_query(query, params)

async def update_payment(payment_id: int, payment_data: dict[str, Any]) -> int:
    """
    Update an existing payment record using the soft-delete pattern.
    
    Returns: ID of the updated payment
    """
    async with db_connection() as conn:
        async with conn.execute("BEGIN") as _:
            try:
                # First, soft-delete the current payment
                delete_query = """
                UPDATE payments 
                SET valid_to = CURRENT_TIMESTAMP 
                WHERE payment_id = ? AND valid_to IS NULL
                """
                await conn.execute(delete_query, (payment_id,))
                
                # Then fetch the existing payment to preserve any fields not being updated
                fetch_query = """
                SELECT * FROM payments
                WHERE payment_id = ?
                """
                cursor = await conn.execute(fetch_query, (payment_id,))
                existing_payment = await cursor.fetchone()
                
                if not existing_payment:
                    await conn.rollback()
                    return 0
                
                # Merge existing data with updates
                merged_data = {**existing_payment, **payment_data}
                
                # Create a new record with the updated data
                create_query = """
                INSERT INTO payments (
                    contract_id, client_id, received_date, total_assets, 
                    expected_fee, actual_fee, method, notes,
                    applied_start_month, applied_start_month_year, 
                    applied_end_month, applied_end_month_year,
                    applied_start_quarter, applied_start_quarter_year,
                    applied_end_quarter, applied_end_quarter_year,
                    valid_from
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """
                
                params = (
                    merged_data.get('contract_id'),
                    merged_data.get('client_id'),
                    merged_data.get('received_date'),
                    merged_data.get('total_assets'),
                    merged_data.get('expected_fee'),
                    merged_data.get('actual_fee'),
                    merged_data.get('method'),
                    merged_data.get('notes'),
                    merged_data.get('applied_start_month'),
                    merged_data.get('applied_start_month_year'),
                    merged_data.get('applied_end_month'),
                    merged_data.get('applied_end_month_year'),
                    merged_data.get('applied_start_quarter'),
                    merged_data.get('applied_start_quarter_year'),
                    merged_data.get('applied_end_quarter'),
                    merged_data.get('applied_end_quarter_year')
                )
                
                cursor = await conn.execute(create_query, params)
                new_payment_id = cursor.lastrowid
                
                await conn.commit()
                return new_payment_id
            except Exception as e:
                await conn.rollback()
                print(f"Payment update error: {str(e)}")
                return 0

async def delete_payment(payment_id: int) -> bool:
    """
    Soft-delete a payment by setting valid_to.
    
    Returns: Boolean indicating success
    """
    query = """
    UPDATE payments 
    SET valid_to = CURRENT_TIMESTAMP 
    WHERE payment_id = ? AND valid_to IS NULL
    """
    
    result = await execute_write_query(query, (payment_id,))
    return result > 0

# backend/app/database/models.py (additions)

async def get_active_contract(client_id: int) -> Optional[dict[str, Any]]:
    """
    Get the active contract for a client.
    
    Args:
        client_id: Client ID
        
    Returns: Active contract record or None
    """
    query = """
    SELECT *
    FROM contracts
    WHERE client_id = ? AND valid_to IS NULL
    """
    
    results = await execute_query(query, (client_id,))
    return results[0] if results else None

async def get_payment(payment_id: int) -> Optional[dict[str, Any]]:
    """
    Get a payment by ID.
    
    Args:
        payment_id: Payment ID
        
    Returns: Payment record or None
    """
    query = """
    SELECT *
    FROM payments
    WHERE payment_id = ? AND valid_to IS NULL
    """
    
    results = await execute_query(query, (payment_id,))
    return results[0] if results else None