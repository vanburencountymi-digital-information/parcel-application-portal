from django.utils import timezone

from ..models import Address
from .exceptions import AddressVerificationError
from .usps import USPSClient

__all__ = ["AddressService"]


class AddressService:
    """Service class for reusable operations on Address records."""

    def __init__(self, address_client: USPSClient | None = None) -> None:
        self._address_client = address_client or USPSClient()

    def verify(self, address: Address) -> dict[str, str]:
        """Verify `address`, save it either way, and return the standardized
        address.

        On success, fills in the standardized_* fields and sets
        is_verified/verified_at before saving, and returns the standardized
        address as a dict (line1/line2/city/state/zip_code). On failure,
        still saves the address as entered (unverified) and raises
        AddressVerificationError.
        """
        try:
            standardized = self._address_client.standardize_address(
                line1=address.line1,
                line2=address.line2,
                city=address.city,
                state=address.state,
                zip_code=address.zip_code,
            )
        except AddressVerificationError:
            address.save()
            raise

        address.standardized_line1 = standardized["line1"]
        address.standardized_line2 = standardized["line2"]
        address.standardized_city = standardized["city"]
        address.standardized_state = standardized["state"]
        address.standardized_zip_code = standardized["zip_code"]
        address.is_verified = True
        address.verified_at = timezone.now()
        address.save()
        return standardized
