"""
Unit tests for billing and cost calculation
"""
from decimal import Decimal
from app.services.billing.metering import calculate_cost


def test_calculate_cost_vendor_a():
    """Test cost calculation for VendorA"""
    # VendorA: $0.002 per 1K tokens
    cost = calculate_cost("vendorA", tokens_in=1000, tokens_out=1000)

    # (1000 / 1000) * 0.002 + (1000 / 1000) * 0.002 = 0.004
    expected = Decimal("0.004")
    assert cost == expected


def test_calculate_cost_vendor_b():
    """Test cost calculation for VendorB"""
    # VendorB: $0.003 per 1K tokens
    cost = calculate_cost("vendorB", tokens_in=500, tokens_out=300)

    # (500 / 1000) * 0.003 + (300 / 1000) * 0.003 = 0.0024
    expected = Decimal("0.0024")
    assert cost == expected


def test_calculate_cost_zero_tokens():
    """Test cost calculation with zero tokens"""
    cost = calculate_cost("vendorA", tokens_in=0, tokens_out=0)
    assert cost == Decimal("0.000000")


def test_calculate_cost_precision():
    """Test cost calculation maintains 6 decimal precision"""
    cost = calculate_cost("vendorA", tokens_in=123, tokens_out=456)

    # (123 / 1000) * 0.002 + (456 / 1000) * 0.002
    # = 0.000246 + 0.000912 = 0.001158
    expected = Decimal("0.001158")
    assert cost == expected


def test_calculate_cost_large_numbers():
    """Test cost calculation with large token counts"""
    cost = calculate_cost("vendorB", tokens_in=100000, tokens_out=50000)

    # (100000 / 1000) * 0.003 + (50000 / 1000) * 0.003
    # = 0.3 + 0.15 = 0.45
    expected = Decimal("0.450000")
    assert cost == expected
