# backend/tests/test_client_service.py
"""
Tests for the client service module.

This test suite focuses on the core business logic functions in the client service:
- determine_payment_status
- calculate_missing_payments
- calculate_expected_fee
"""
import pytest
from datetime import datetime, timedelta
from app.services.client_service import (
    determine_payment_status,
    calculate_missing_payments,
    calculate_expected_fee
)
from app.utils.enums import FeeType, PaymentSchedule

# Mock data for testing
def create_test_client(payment_schedule, last_month=None, last_year=None, 
                       last_quarter=None, fee_type=FeeType.PERCENTAGE, 
                       rate=0.0075, last_recorded_aum=1000000):
    """Helper to create test client data"""
    client = {
        "paymentSchedule": payment_schedule,
        "lastPaymentMonth": last_month,
        "lastPaymentYear": last_year,
        "lastPaymentQuarter": last_quarter,
        "feeType": fee_type,
        "rate": rate,
        "lastRecordedAUM": last_recorded_aum
    }
    return client

class TestDeterminePaymentStatus:
    """Tests for the determine_payment_status function"""
    
    def test_monthly_current_payment(self):
        """Test monthly client with current payment"""
        # Get current month/year
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        # Create client with current payment
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            last_month=current_month,
            last_year=current_year
        )
        
        # Should be paid
        assert determine_payment_status(client) == "Paid"
    
    def test_monthly_missing_payment(self):
        """Test monthly client with missing payment"""
        # Get current date minus 2 months
        today = datetime.now()
        two_months_ago = today - timedelta(days=60)
        
        # Create client with payment from 2 months ago
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            last_month=two_months_ago.month,
            last_year=two_months_ago.year
        )
        
        # Should be due
        assert determine_payment_status(client) == "Due"
    
    def test_quarterly_current_payment(self):
        """Test quarterly client with current payment"""
        # Get current quarter
        today = datetime.now()
        current_quarter = ((today.month - 1) // 3) + 1
        current_year = today.year
        
        # Create client with current payment
        client = create_test_client(
            payment_schedule=PaymentSchedule.QUARTERLY,
            last_quarter=current_quarter,
            last_year=current_year
        )
        
        # Should be paid
        assert determine_payment_status(client) == "Paid"
    
    def test_quarterly_missing_payment(self):
        """Test quarterly client with missing payment"""
        # Get current date minus 6 months (2 quarters)
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        past_quarter = ((six_months_ago.month - 1) // 3) + 1
        
        # Create client with payment from 2 quarters ago
        client = create_test_client(
            payment_schedule=PaymentSchedule.QUARTERLY,
            last_quarter=past_quarter,
            last_year=six_months_ago.year
        )
        
        # Should be due
        assert determine_payment_status(client) == "Due"
    
    def test_no_payment_history(self):
        """Test client with no payment history"""
        # Create client with no payment history
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            last_month=None,
            last_year=None
        )
        
        # Should be due
        assert determine_payment_status(client) == "Due"

class TestCalculateExpectedFee:
    """Tests for the calculate_expected_fee function"""
    
    def test_percentage_fee_calculation(self):
        """Test percentage fee calculation"""
        # Create percentage fee client
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            fee_type=FeeType.PERCENTAGE,
            rate=0.0075,  # 0.75%
            last_recorded_aum=1000000
        )
        
        # Expected fee: 1,000,000 * 0.0075 = 7,500
        expected_fee = calculate_expected_fee(client)
        assert expected_fee == 7500.0
    
    def test_flat_fee_calculation(self):
        """Test flat fee calculation"""
        # Create flat fee client
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            fee_type=FeeType.FLAT,
            rate=5000,  # $5,000 flat fee
            last_recorded_aum=1000000  # Should be ignored
        )
        
        # Expected fee should be the flat rate
        expected_fee = calculate_expected_fee(client)
        assert expected_fee == 5000
    
    def test_missing_data_returns_none(self):
        """Test handling of missing data"""
        # Create client with missing rate
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            fee_type=FeeType.PERCENTAGE,
            rate=None,
            last_recorded_aum=1000000
        )
        
        # Should return None if data is missing
        assert calculate_expected_fee(client) is None

class TestCalculateMissingPayments:
    """Tests for the calculate_missing_payments function"""
    
    def test_no_missing_payments(self):
        """Test when client is current (no missing payments)"""
        # Get current month/year
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        # Create client with current payment
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            last_month=current_month,
            last_year=current_year
        )
        
        # Should return empty list
        missing = calculate_missing_payments(client)
        assert missing == []
    
    def test_monthly_missing_payments(self):
        """Test when monthly client has missing payments"""
        # Get date from 3 months ago
        today = datetime.now()
        three_months_ago = today - timedelta(days=90)
        
        # Create client with payment from 3 months ago
        client = create_test_client(
            payment_schedule=PaymentSchedule.MONTHLY,
            last_month=three_months_ago.month,
            last_year=three_months_ago.year
        )
        
        # Should return list of missing periods
        missing = calculate_missing_payments(client)
        
        # Validate result
        assert len(missing) > 0
        # We expect approximately 2-3 missing periods (depending on month lengths)
        assert 1 <= len(missing) <= 3
    
    def test_quarterly_missing_payments(self):
        """Test when quarterly client has missing payments"""
        # Get date from 6 months ago (2 quarters)
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        past_quarter = ((six_months_ago.month - 1) // 3) + 1
        
        # Create client with payment from 2 quarters ago
        client = create_test_client(
            payment_schedule=PaymentSchedule.QUARTERLY,
            last_quarter=past_quarter,
            last_year=six_months_ago.year
        )
        
        # Should return list of missing quarters
        missing = calculate_missing_payments(client)
        
        # Validate result
        assert len(missing) > 0
        # We expect approximately 1-2 missing quarters
        assert 1 <= len(missing) <= 2