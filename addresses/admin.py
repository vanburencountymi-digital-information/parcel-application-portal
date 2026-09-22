from django.contrib import admin

from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["line1", "city", "state", "zip_code", "is_verified", "created_at"]
    list_filter = ["is_verified", "state"]
