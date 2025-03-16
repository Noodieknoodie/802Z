# backend/app/utils/enums.py
"""
Enumeration types used throughout the application.
"""
from enum import Enum

class FeeType(str, Enum):
    """Fee type enumeration"""
    PERCENTAGE = "percentage"
    FLAT = "flat"

class PaymentSchedule(str, Enum):
    """Payment schedule enumeration"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    ACH = "Auto - ACH"
    CHECK = "Check"
    WIRE = "Wire"
    INVOICE = "Invoice"