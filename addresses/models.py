from django.db import models
from localflavor.us.models import USStateField, USZipCodeField


class Address(models.Model):
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state = USStateField()
    zip_code = USZipCodeField()

    # Filled in from the USPS standardization response once verified.
    standardized_line1 = models.CharField(max_length=255, blank=True)
    standardized_line2 = models.CharField(max_length=255, blank=True)
    standardized_city = models.CharField(max_length=255, blank=True)
    standardized_state = USStateField(blank=True)
    standardized_zip_code = USZipCodeField(blank=True)

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self) -> str:
        return f"{self.line1}, {self.city}, {self.state} {self.zip_code}"
