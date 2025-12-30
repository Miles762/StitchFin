"""
Unit tests for vendor adapters
"""
import pytest
from app.services.vendors.vendor_a import VendorA, VendorAHTTPError
from app.services.vendors.vendor_b import VendorB, VendorBRateLimitError
from app.services.vendors.base import VendorRequest


@pytest.mark.asyncio
async def test_vendor_a_success():
    """Test VendorA successful response"""
    vendor = VendorA()
    request = VendorRequest(
        system_prompt="You are a helpful assistant",
        user_message="Hello"
    )

    # May fail due to 10% failure rate, retry until success
    max_attempts = 20
    success = False

    for _ in range(max_attempts):
        try:
            response = await vendor.send_message(request)
            success = True
            assert "outputText" in response
            assert "tokensIn" in response
            assert "tokensOut" in response
            assert "latencyMs" in response
            assert response["tokensIn"] > 0
            assert response["tokensOut"] > 0
            break
        except VendorAHTTPError:
            continue

    assert success, "VendorA should eventually succeed"


@pytest.mark.asyncio
async def test_vendor_a_normalization():
    """Test VendorA response normalization"""
    vendor = VendorA()

    raw_response = {
        "outputText": "Test response",
        "tokensIn": 10,
        "tokensOut": 20,
        "latencyMs": 100
    }

    normalized = vendor.normalize_response(raw_response)

    assert normalized.text == "Test response"
    assert normalized.tokens_in == 10
    assert normalized.tokens_out == 20
    assert normalized.latency_ms == 100


@pytest.mark.asyncio
async def test_vendor_b_success():
    """Test VendorB successful response"""
    vendor = VendorB()
    request = VendorRequest(
        system_prompt="You are a helpful assistant",
        user_message="Hello"
    )

    # May fail due to 15% rate limit, retry until success
    max_attempts = 20
    success = False

    for _ in range(max_attempts):
        try:
            response = await vendor.send_message(request)
            success = True
            assert "choices" in response
            assert "usage" in response
            assert len(response["choices"]) > 0
            assert "message" in response["choices"][0]
            assert "content" in response["choices"][0]["message"]
            break
        except VendorBRateLimitError:
            continue

    assert success, "VendorB should eventually succeed"


@pytest.mark.asyncio
async def test_vendor_b_normalization():
    """Test VendorB response normalization"""
    vendor = VendorB()

    raw_response = {
        "choices": [
            {
                "message": {
                    "content": "Test response from VendorB"
                }
            }
        ],
        "usage": {
            "input_tokens": 15,
            "output_tokens": 25
        },
        "latency_ms": 200
    }

    normalized = vendor.normalize_response(raw_response)

    assert normalized.text == "Test response from VendorB"
    assert normalized.tokens_in == 15
    assert normalized.tokens_out == 25
    assert normalized.latency_ms == 200
