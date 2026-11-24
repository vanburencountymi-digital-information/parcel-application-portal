class AssessorValidationError(ValueError):
    """The assessor could not be created (bad or duplicate email, bad phone number).

    The message is written for the admin filling in the form, so views can show it as-is.
    """
