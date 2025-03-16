# backend/app/utils/format.py
"""
Data formatting utilities.

Provides consistent formatting for:
- Dates
- Currency values
- Percentages
- Period representations
"""
from datetime import datetime
from typing import Any, Optional, Union

from app.utils.enums import PaymentSchedule

# Month name mapping
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

# Month number mapping (reverse lookup)
MONTH_NUMBERS = {v: k for k, v in MONTH_NAMES.items()}

def format_date(date_str: Optional[str]) -> Optional[str]:
    """
    Format date strings consistently for frontend display.
    
    Returns: Formatted date string (MM/DD/YYYY) or None
    """
    if not date_str:
        return None
    
    try:
        # Parse date (handle both database and display formats)
        if "-" in date_str:
            # YYYY-MM-DD format
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        elif "/" in date_str:
            # MM/DD/YYYY format
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        else:
            return date_str  # Return as is if format unknown
        
        # Format consistently for frontend
        return date_obj.strftime("%m/%d/%Y")
    except ValueError:
        # Return original if parsing fails
        return date_str

def format_month_name(month_num: int) -> str:
    """Convert month number to three-letter abbreviation."""
    return MONTH_NAMES.get(month_num, "")

def format_period(schedule: str, value: int, year: int) -> str:
    """
    Format period based on payment schedule.
    
    Returns: Formatted period string
    """
    if schedule.lower() == PaymentSchedule.MONTHLY:
        month_name = format_month_name(value)
        return f"{month_name} {year}"
    elif schedule.lower() == PaymentSchedule.QUARTERLY:
        return f"Q{value} {year}"
    return ""

def parse_period(period_str: str, payment_schedule: str) -> dict[str, Any]:
    """
    Parse frontend period format into database fields.
    
    Returns: Dictionary with appropriate period fields for database insertion
    """
    result = {}
    
    if payment_schedule.lower() == PaymentSchedule.MONTHLY:
        # Parse monthly period like "Jan 2024"
        parts = period_str.split()
        if len(parts) == 2:
            month_str, year_str = parts
            month_num = MONTH_NUMBERS.get(month_str, 1)
            year = int(year_str)
            
            result.update({
                "applied_start_month": month_num,
                "applied_start_month_year": year,
                "applied_end_month": month_num,
                "applied_end_month_year": year
            })
    
    elif payment_schedule.lower() == PaymentSchedule.QUARTERLY:
        # Parse quarterly period like "Q1 2024"
        parts = period_str.strip().split()
        if len(parts) == 2:
            quarter_str, year_str = parts
            quarter = int(quarter_str[1:])  # Remove "Q" prefix
            year = int(year_str)
            
            result.update({
                "applied_start_quarter": quarter,
                "applied_start_quarter_year": year,
                "applied_end_quarter": quarter,
                "applied_end_quarter_year": year
            })
    
    return result

def format_currency(value: Optional[Union[int, float]]) -> Optional[str]:
    """
    Format currency values consistently.
    
    Returns: Formatted currency string or None
    """
    if value is None:
        return None
    
    try:
        # Format with commas for thousands and 2 decimal places
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return str(value)

def format_percentage(value: Optional[Union[int, float]]) -> Optional[str]:
    """
    Format percentage values consistently.
    
    Returns: Formatted percentage string
    """
    if value is None:
        return None
    
    try:
        # Convert value to float
        float_value = float(value)
        
        # If value is less than 1 and likely a decimal percentage (e.g., 0.05 for 5%)
        if float_value < 1 and float_value > 0:
            float_value *= 100
            
        # Format with 2 decimal places and % symbol
        return f"{float_value:.2f}%"
    except (ValueError, TypeError):
        return str(value)