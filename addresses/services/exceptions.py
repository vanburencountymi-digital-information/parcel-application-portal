class AddressVerificationError(Exception):
    """Raised by an address client when an address could not be verified.
    Any client AddressService is given (CensusGeocoderClient or otherwise) should raise
    this directly, so AddressService never needs to know about a specific
    provider's own exception types.
    """
