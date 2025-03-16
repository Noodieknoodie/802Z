# backend/tests/test_payment_service.py
"""
Tests for the payment service module.

This test suite focuses on the payment service functions:
- parse_frontend_period
- parse_multi_period
- count_periods
- calculate_expected_fee
- validate_payment_data
- prepare_payment_data
"""
import pytest
from datetime import datetime
import asyncio
from app.services.payment_service import (
    parse_frontend_period,
    parse_multi_period,
    count_periods,
    validate_payment_data
)
from app.utils.enums import PaymentSchedule, PaymentMethod

# Mock the database functions
@pytest.fixture
def mock_db(monkeypatch):
    """Mock database functions used by the service"""
    # Mock get_client_details
    async def mock_get_client_details(client_id):
        return {
            "id": client_id,
            "feeType": "percentage",
            "rate": 0.0075,
            "paymentSchedule": "monthly",
            "lastRecordedAUM": 1000000
        }
    
    # Mock get_active_contract
    async def mock_get_active_contract(client_id):
        return {
            "contract_id": 1,
            "client_id": client_id,
            "fee_type": "percentage",
            "percent_rate": 0.0075,
            "payment_schedule": "monthly"
        }
    
    # Apply mocks
    from app.database import models
    monkeypatch.setattr(models, "get_client_details", mock_get_client_details)
    monkeypatch.setattr(models, "get_active_contract", mock_get_active_contract)

class TestParsePeriod:
    """Tests for period parsing functions"""
    
    @pytest.mark.asyncio
    async def test_parse_monthly_period(self):
        """Test parsing a monthly period string"""
        result = await parse_frontend_period("Jan 2024", PaymentSchedule.MONTHLY)
        
        assert "applied_start_month" in result
        assert result["applied_start_month"] == 1
        assert result["applied_start_month_year"] == 2024
        assert result["applied_end_month"] == 1
        assert result["applied_end_month_year"] == 2024
    
    @pytest.mark.asyncio
    async def test_parse_quarterly_period(self):
        """Test parsing a quarterly period string"""
        result = await parse_frontend_period("Q2 2024", PaymentSchedule.QUARTERLY)
        
        assert "applied_start_quarter" in result
        assert result["applied_start_quarter"] == 2
        assert result["applied_start_quarter_year"] == 2024
        assert result["applied_end_quarter"] == 2
        assert result["applied_end_quarter_year"] == 2024
    
    @pytest.mark.asyncio
    async def test_parse_multi_period_monthly(self):
        """Test parsing monthly multi-period"""
        result = await parse_multi_period("Jan 2024", "Mar 2024", PaymentSchedule.MONTHLY)
        
        assert result["applied_start_month"] == 1
        assert result["applied_start_month_year"] == 2024
        assert result["applied_end_month"] == 3
        assert result["applied_end_month_year"] == 2024
        assert result["applied_start_quarter"] is None
    
    @pytest.mark.asyncio
    async def test_parse_multi_period_quarterly(self):
        """Test parsing quarterly multi-period"""
        result = await parse_multi_period("Q1 2024", "Q3 2024", PaymentSchedule.QUARTERLY)
        
        assert result["applied_start_quarter"] == 1
        assert result["applied_start_quarter_year"] == 2024
        assert result["applied_end_quarter"] == 3
        assert result["applied_end_quarter_year"] == 2024
        assert result["applied_start_month"] is None

class TestCountPeriods:
    """Tests for period counting"""
    
    @pytest.mark.asyncio
    async def test_count_monthly_periods_same_year(self):
        """Test counting monthly periods within same year"""
        payment_data = {
            "payment_schedule": PaymentSchedule.MONTHLY,
            "applied_start_month": 1,
            "applied_start_month_year": 2024,
            "applied_end_month": 3,
            "applied_end_month_year": 2024
        }
        
        count = await count_periods(payment_data)
        assert count == 3  # Jan, Feb, Mar = 3 months
    
    @pytest.mark.asyncio
    async def test_count_monthly_periods_across_years(self):
        """Test counting monthly periods across year boundary"""
        payment_data = {
            "payment_schedule": PaymentSchedule.MONTHLY,
            "applied_start_month": 11,
            "applied_start_month_year": 2023,
            "applied_end_month": 2,
            "applied_end_month_year": 2024
        }
        
        count = await count_periods(payment_data)
        assert count == 4  # Nov, Dec, Jan, Feb = 4 months
    
    @pytest.mark.asyncio
    async def test_count_quarterly_periods(self):
        """Test counting quarterly periods"""
        payment_data = {
            "payment_schedule": PaymentSchedule.QUARTERLY,
            "applied_start_quarter": 3,
            "applied_start_quarter_year": 2023,
            "applied_end_quarter": 2,
            "applied_end_quarter_year": 2024
        }
        
        count = await count_periods(payment_data)
        assert count == 4  # Q3 2023, Q4 2023, Q1 2024, Q2 2024 = 4 quarters

class TestValidatePaymentData:
    """Tests for payment data validation"""
    
    @pytest.mark.asyncio
    async def test_valid_payment_data(self):
        """Test validation of valid payment data"""
        payment_data = {
            "client_id": 1,
            "contract_id": 1,
            "received_date": "2024-03-15",
            "actual_fee": 7500.0,
            "total_assets": 1000000,
            "method": PaymentMethod.ACH,
            "notes": "Test payment"
        }
        
        is_valid, error_message = await validate_payment_data(payment_data)
        assert is_valid
        assert error_message is None
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test validation fails with missing fields"""
        payment_data = {
            "client_id": 1,
            # Missing contract_id and received_date
            "actual_fee": 7500.0
        }
        
        is_valid, error_message = await validate_payment_data(payment_data)
        assert not is_valid
        assert "Missing required fields" in error_message
    
    @pytest.mark.asyncio
    async def test_invalid_payment_method(self):
        """Test validation fails with invalid payment method"""
        payment_data = {
            "client_id": 1,
            "contract_id": 1,
            "received_date": "2024-03-15",
            "actual_fee": 7500.0,
            "method": "Invalid Method"  # Invalid method
        }
        
        is_valid, error_message = await validate_payment_data(payment_data)
        assert not is_valid
        assert "Invalid payment method" in error_message
    
    @pytest.mark.asyncio
    async def test_invalid_date_format(self):
        """Test validation fails with invalid date format"""
        payment_data = {
            "client_id": 1,
            "contract_id": 1,
            "received_date": "15/03/2024",  # Wrong format, should be YYYY-MM-DD
            "actual_fee": 7500.0
        }
        
        is_valid, error_message = await validate_payment_data(payment_data)
        assert not is_valid
        assert "Invalid date format" in error_message
    
    @pytest.mark.asyncio
    async def test_negative_values(self):
        """Test validation fails with negative numeric values"""
        payment_data = {
            "client_id": 1,
            "contract_id": 1,
            "received_date": "2024-03-15",
            "actual_fee": -7500.0,  # Negative value
            "total_assets": 1000000
        }
        
        is_valid, error_message = await validate_payment_data(payment_data)
        assert not is_valid
        assert "cannot be negative" in error_message