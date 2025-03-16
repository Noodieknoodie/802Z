# backend/app/services/payment_service.py
"""
Payment business logic.

Handles complex payment-related operations:
- Payment creation with proper period handling
- Expected fee calculation
- Multi-period payment handling
"""
from typing import Any, Optional
from datetime import datetime

from app.utils.format import parse_period, format_period
from app.utils.enums import FeeType, PaymentSchedule, PaymentMethod

async def parse_frontend_period(period_str: str, payment_schedule: str) -> dict[str, Any]:
    """
    Parse frontend period format into database fields.
    
    Args:
        period_str: Frontend period format (e.g., "Jan 2024" or "Q1 2024")
        payment_schedule: "monthly" or "quarterly"
        
    Returns: Dictionary with appropriate period fields for database insertion
    """
    return parse_period(period_str, payment_schedule)

async def parse_multi_period(start_period: str, end_period: str, payment_schedule: str) -> dict[str, Any]:
    """
    Parse multi-period selection into database fields.
    
    Args:
        start_period: Start period in frontend format (e.g., "Jan 2024")
        end_period: End period in frontend format (e.g., "Mar 2024")
        payment_schedule: "monthly" or "quarterly"
        
    Returns: Dictionary with period fields for database insertion
    """
    # Parse start and end periods
    start_fields = parse_period(start_period, payment_schedule)
    end_fields = parse_period(end_period, payment_schedule)
    
    # Combine into a single result
    result = {}
    
    if payment_schedule.lower() == PaymentSchedule.MONTHLY:
        result.update({
            "applied_start_month": start_fields.get("applied_start_month"),
            "applied_start_month_year": start_fields.get("applied_start_month_year"),
            "applied_end_month": end_fields.get("applied_start_month"),
            "applied_end_month_year": end_fields.get("applied_start_month_year"),
            # Set quarterly fields to NULL
            "applied_start_quarter": None,
            "applied_start_quarter_year": None,
            "applied_end_quarter": None,
            "applied_end_quarter_year": None
        })
    elif payment_schedule.lower() == PaymentSchedule.QUARTERLY:
        result.update({
            "applied_start_quarter": start_fields.get("applied_start_quarter"),
            "applied_start_quarter_year": start_fields.get("applied_start_quarter_year"),
            "applied_end_quarter": end_fields.get("applied_start_quarter"),
            "applied_end_quarter_year": end_fields.get("applied_start_quarter_year"),
            # Set monthly fields to NULL
            "applied_start_month": None,
            "applied_start_month_year": None,
            "applied_end_month": None,
            "applied_end_month_year": None
        })
    
    return result
    
async def count_periods(payment_data: dict[str, Any]) -> int:
    """
    Count the number of periods covered by a payment.
    
    Args:
        payment_data: Payment data with period fields
        
    Returns: Number of periods covered
    """
    payment_schedule = payment_data.get("payment_schedule", "").lower()
    
    if payment_schedule == PaymentSchedule.MONTHLY:
        start_month = payment_data.get("applied_start_month")
        start_year = payment_data.get("applied_start_month_year")
        end_month = payment_data.get("applied_end_month")
        end_year = payment_data.get("applied_end_month_year")
        
        if start_month is None or start_year is None or end_month is None or end_year is None:
            return 1  # Default to single period if data is missing
        
        # Calculate total months between start and end
        return (end_year - start_year) * 12 + (end_month - start_month) + 1
    
    elif payment_schedule == PaymentSchedule.QUARTERLY:
        start_quarter = payment_data.get("applied_start_quarter")
        start_year = payment_data.get("applied_start_quarter_year")
        end_quarter = payment_data.get("applied_end_quarter")
        end_year = payment_data.get("applied_end_quarter_year")
        
        if start_quarter is None or start_year is None or end_quarter is None or end_year is None:
            return 1  # Default to single period if data is missing
        
        # Calculate total quarters between start and end
        return (end_year - start_year) * 4 + (end_quarter - start_quarter) + 1
    
    return 1  # Default to single period for unknown schedule

async def calculate_expected_fee(client_id: int, payment_data: dict[str, Any]) -> float:
    """
    Calculate the expected fee based on client fee structure and assets.
    
    Args:
        client_id: Client ID
        payment_data: Payment data with assets and period information
        
    Returns: Expected fee as a decimal value
    """
    from app.database.models import get_client_details
    
    # Get client contract details
    client = await get_client_details(client_id)
    if not client:
        return 0.0
    
    # Extract fee structure
    fee_type = client.get("feeType", "")
    rate = client.get("rate", 0.0)
    total_assets = payment_data.get("total_assets", 0)
    
    # Count number of periods covered by this payment
    num_periods = await count_periods(payment_data)
    
    # Calculate expected fee based on fee type
    if fee_type == FeeType.PERCENTAGE:
        # For percentage fee: assets * rate * num_periods
        expected_fee = total_assets * rate * num_periods
    elif fee_type == FeeType.FLAT:
        # For flat fee: rate * num_periods
        expected_fee = rate * num_periods
    else:
        expected_fee = 0.0
    
    return round(expected_fee, 2)

async def validate_payment_data(payment_data: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate payment data before creation/update.
    
    Args:
        payment_data: Payment data to validate
        
    Returns: Tuple of (is_valid, error_message)
    """
    # Required fields
    required_fields = ["client_id", "contract_id", "received_date", "actual_fee"]
    missing_fields = [field for field in required_fields if field not in payment_data or payment_data[field] is None]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate payment method
    method = payment_data.get("method")
    if method and not any(method == m.value for m in PaymentMethod):
        valid_methods = ", ".join([m.value for m in PaymentMethod])
        return False, f"Invalid payment method. Valid options are: {valid_methods}"
    
    # Validate dates
    try:
        if "received_date" in payment_data:
            # Ensure date is in ISO format (YYYY-MM-DD)
            received_date = payment_data["received_date"]
            if isinstance(received_date, str):
                datetime.strptime(received_date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD format."
    
    # Validate numeric fields
    for field in ["total_assets", "expected_fee", "actual_fee"]:
        if field in payment_data and payment_data[field] is not None:
            try:
                value = float(payment_data[field])
                if value < 0:
                    return False, f"{field} cannot be negative"
            except (ValueError, TypeError):
                return False, f"Invalid value for {field}. Must be a number."
    
    return True, None

async def prepare_payment_data(payment_data: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare payment data for database insertion.
    
    Args:
        payment_data: Raw payment data from frontend
        
    Returns: Processed payment data ready for database
    """
    # Get client and contract information
    from app.database.models import get_client_details
    
    client_id = payment_data.get("client_id")
    if not client_id:
        raise ValueError("client_id is required")
    
    # Process period data
    is_multi_period = payment_data.get("is_multi_period", False)
    client = await get_client_details(client_id)
    payment_schedule = client.get("paymentSchedule", "monthly").lower()
    
    if is_multi_period:
        start_period = payment_data.get("start_period")
        end_period = payment_data.get("end_period")
        if not start_period or not end_period:
            raise ValueError("start_period and end_period are required for multi-period payments")
        
        # Parse multi-period data
        period_fields = await parse_multi_period(start_period, end_period, payment_schedule)
    else:
        period = payment_data.get("period")
        if not period:
            raise ValueError("period is required for single-period payments")
        
        # Parse single period data
        period_fields = await parse_frontend_period(period, payment_schedule)
    
    # Calculate expected fee if not provided
    if "expected_fee" not in payment_data:
        payment_data_with_period = {**payment_data, **period_fields, "payment_schedule": payment_schedule}
        payment_data["expected_fee"] = await calculate_expected_fee(client_id, payment_data_with_period)
    
    # Merge period fields into payment data
    result = {**payment_data, **period_fields, "payment_schedule": payment_schedule}
    
    # Ensure we have contract_id
    if "contract_id" not in result and client:
        # Get latest active contract for this client
        from app.database.models import get_active_contract
        contract = await get_active_contract(client_id)
        if contract:
            result["contract_id"] = contract.get("contract_id")
    
    return result