from django.contrib import admin

from applications.models import AssessingUnit


@admin.register(AssessingUnit)
class AssessingUnitAdmin(admin.ModelAdmin[AssessingUnit]):
    """Lets staff add and edit townships and cities."""

    list_display = ["name", "kind", "parcel_unit_code"]
    list_filter = ["kind"]
    search_fields = ["name", "parcel_unit_code"]
