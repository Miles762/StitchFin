"""
Vendor factory - creates vendor adapter instances
"""
from app.services.vendors.base import VendorAdapter
from app.services.vendors.vendor_a import VendorA
from app.services.vendors.vendor_b import VendorB


def get_vendor_adapter(provider: str) -> VendorAdapter:
    """
    Factory function to get vendor adapter instance

    Args:
        provider: Vendor identifier ('vendorA' or 'vendorB')

    Returns:
        VendorAdapter instance

    Raises:
        ValueError: If provider is not supported
    """
    vendors = {
        "vendorA": VendorA,
        "vendorB": VendorB,
    }

    vendor_class = vendors.get(provider)
    if not vendor_class:
        raise ValueError(f"Unsupported vendor: {provider}")

    return vendor_class()
