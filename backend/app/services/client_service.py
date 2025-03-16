# backend/app/services/client_service.py
"""
Client business logic.

Handles complex client-related operations:
- Data aggregation from multiple tables
- Formatting for frontend consumption
- Missing payment detection
- Status determination
"""
from typing import Any
from datetime import datetime
import json
import asyncio

from app.utils.format import format_period, format_month_name
from app.utils.enums import FeeType, PaymentSchedule

async def get_frontend_client_data() -> dict[str, Any]:
    """
    Build the complete frontend data structure for clients.
    Combines clients, providers, client details, and payment history.
    
    Returns the complete JSON structure with clients, providers, clientDetails, 
    and paymentHistory objects.
    """
    from app.database.models import (
        get_all_clients, 
        get_providers, 
        get_client_details,
        get_client_payment_history
    )
    
    # Get primary data
    clients = await get_all_clients()
    providers = await get_providers()
    
    # Initialize containers for detailed data
    client_details = {}
    payment_history = {}
    
    # For each client, fetch detailed information
    for client in clients:
        client_id = client["id"]
        client_id_str = str(client_id)
        
        # Use tasks for parallel execution
        details_task = asyncio.create_task(get_client_details(client_id))
        payment_history_task = asyncio.create_task(get_client_payment_history(client_id))
        
        # Await both tasks
        client_details[client_id_str] = await details_task
        payment_history_result = await payment_history_task
        payment_history[client_id_str] = payment_history_result["payments"]
    
    # Return the complete structure
    return {
        "clients": clients,
        "providers": providers,
        "clientDetails": client_details,
        "paymentHistory": payment_history
    }

def determine_payment_status(client_data: dict[str, Any]) -> str:
    """Determine if client payments are current or due based on payment schedule."""
    # Get today's date
    today = datetime.now()
    
    # Extract payment schedule and last payment details
    payment_schedule = client_data.get("paymentSchedule", "").lower()
    
    # Calculate previous period (the period that should be paid by now)
    if payment_schedule == PaymentSchedule.MONTHLY:
        # Calculate current period (previous month)
        if today.month == 1:
            current_period_month = 12
            current_period_year = today.year - 1
        else:
            current_period_month = today.month - 1
            current_period_year = today.year
            
        # Extract client's last payment month/year
        last_payment_month = client_data.get("lastPaymentMonth")
        last_payment_year = client_data.get("lastPaymentYear")
        
        # Compare periods
        if last_payment_month is None or last_payment_year is None:
            return "Due"  # No payments yet
        
        if (last_payment_year < current_period_year or 
            (last_payment_year == current_period_year and 
             last_payment_month < current_period_month)):
            return "Due"  # Last payment is before current period
        else:
            return "Paid"  # Last payment is current or newer
            
    elif payment_schedule == PaymentSchedule.QUARTERLY:
        # Calculate current quarter
        current_period_quarter = ((today.month - 1) // 3) + 1
        current_period_year = today.year
        
        # If we're in Q1, the previous quarter was Q4 of last year
        if current_period_quarter == 1:
            current_period_quarter = 4
            current_period_year = today.year - 1
        else:
            current_period_quarter -= 1
            
        # Extract client's last payment quarter/year
        last_payment_quarter = client_data.get("lastPaymentQuarter")
        last_payment_year = client_data.get("lastPaymentYear")
        
        # Compare periods
        if last_payment_quarter is None or last_payment_year is None:
            return "Due"  # No payments yet
        
        if (last_payment_year < current_period_year or 
            (last_payment_year == current_period_year and 
             last_payment_quarter < current_period_quarter)):
            return "Due"  # Last payment is before current period
        else:
            return "Paid"  # Last payment is current or newer
    
    return "Due"  # Default to Due if payment schedule is unknown

def calculate_expected_fee(client_data: dict[str, Any]) -> float:
    """
    Calculate expected fee based on fee type and rates.
    
    Returns: Calculated fee as a decimal number, or None if calculation not possible
    """
    fee_type = client_data.get("feeType", "")
    
    if fee_type == FeeType.PERCENTAGE:
        # Get percentage rate (already stored as decimal)
        percent_rate = client_data.get("rate")
        assets = client_data.get("lastRecordedAUM")
        
        if percent_rate is not None and assets is not None:
            # Direct multiplication (rate is already decimal)
            return round(assets * percent_rate, 2)
    
    elif fee_type == FeeType.FLAT:
        # For flat fee, just return the rate
        return client_data.get("rate")
    
    return None

def calculate_missing_payments(client_data: dict[str, Any]) -> list[str]:
    """
    Generate a list of missing payment periods for frontend status display.
    
    Returns: Array of formatted period strings representing missing payments,
    or empty array if client is current
    """
    # If payment status is "Paid", return empty array (no missing payments)
    if determine_payment_status(client_data) == "Paid":
        return []
    
    # Get today's date
    today = datetime.now()
    
    # Container for missing payment periods
    missing_periods = []
    
    # Extract payment schedule
    payment_schedule = client_data.get("paymentSchedule", "").lower()
    
    if payment_schedule == PaymentSchedule.MONTHLY:
        # Extract client's last payment month/year
        last_month = client_data.get("lastPaymentMonth", 0)
        last_year = client_data.get("lastPaymentYear", 0)
        
        # Calculate the next period after the last payment
        if last_month == 12:
            next_month = 1
            next_year = last_year + 1
        else:
            next_month = last_month + 1
            next_year = last_year
        
        # Calculate current period (previous month)
        if today.month == 1:
            current_month = 12
            current_year = today.year - 1
        else:
            current_month = today.month - 1
            current_year = today.year
        
        # Generate all missing periods
        current_month_iter = next_month
        current_year_iter = next_year
        
        while (current_year_iter < current_year or 
               (current_year_iter == current_year and current_month_iter <= current_month)):
            # Format the period string
            period_str = format_period("monthly", current_month_iter, current_year_iter)
            missing_periods.append(period_str)
            
            # Move to next month
            if current_month_iter == 12:
                current_month_iter = 1
                current_year_iter += 1
            else:
                current_month_iter += 1
                
    elif payment_schedule == PaymentSchedule.QUARTERLY:
        # Extract client's last payment quarter/year
        last_quarter = client_data.get("lastPaymentQuarter", 0)
        last_year = client_data.get("lastPaymentYear", 0)
        
        # Calculate the next period after the last payment
        if last_quarter == 4:
            next_quarter = 1
            next_year = last_year + 1
        else:
            next_quarter = last_quarter + 1
            next_year = last_year
        
        # Calculate current period (current quarter)
        current_quarter = ((today.month - 1) // 3) + 1
        current_year = today.year
        
        # If we're in the first month of a quarter, the previous quarter is the one to check
        if today.month % 3 == 1:
            if current_quarter == 1:
                current_quarter = 4
                current_year -= 1
            else:
                current_quarter -= 1
        
        # Generate all missing periods
        current_quarter_iter = next_quarter
        current_year_iter = next_year
        
        while (current_year_iter < current_year or 
               (current_year_iter == current_year and current_quarter_iter <= current_quarter)):
            # Format the period string
            period_str = format_period("quarterly", current_quarter_iter, current_year_iter)
            missing_periods.append(period_str)
            
            # Move to next quarter
            if current_quarter_iter == 4:
                current_quarter_iter = 1
                current_year_iter += 1
            else:
                current_quarter_iter += 1
    
    return missing_periods