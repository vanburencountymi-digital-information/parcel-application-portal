from typing import Any

from django import forms
from django.contrib import admin
from django.http import HttpRequest

from applications.exceptions import AssessorValidationError
from applications.models import AssessingUnit, Assessor
from applications.services import AssessorService


@admin.register(AssessingUnit)
class AssessingUnitAdmin(admin.ModelAdmin[AssessingUnit]):
    """Lets staff add and edit townships and cities."""

    list_display = ["name", "kind", "parcel_unit_code"]
    list_filter = ["kind"]
    search_fields = ["name", "parcel_unit_code"]


class AssessorAddForm(forms.ModelForm[Assessor]):
    """Add form for an assessor. It creates the user too, through `AssessorService`."""

    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Assessor
        fields = ["phone_number", "assessing_units", "is_active"]

    def clean(self) -> dict[str, Any]:
        """Creates the user and assessor once every field is valid.

        Takes: nothing (reads the submitted fields).
        Returns: the cleaned data (dict). A problem the service finds, such as an email
        already in use, is shown as a form error. The saved assessor becomes the form's
        instance, so the admin's own save only updates it.
        """
        cleaned_data = super().clean() or {}
        if self.errors:
            return cleaned_data
        try:
            self.instance = AssessorService().create(
                email=cleaned_data["email"],
                assessing_units=cleaned_data["assessing_units"],
                first_name=cleaned_data["first_name"],
                last_name=cleaned_data["last_name"],
                phone_number=str(cleaned_data["phone_number"] or ""),
                is_active=cleaned_data["is_active"],
            )
        except AssessorValidationError as error:
            self.add_error(None, str(error))
        return cleaned_data


@admin.register(Assessor)
class AssessorAdmin(admin.ModelAdmin[Assessor]):
    """Lets staff add assessors and edit their units, phone number and active flag.

    Name and email are read-only once created: change them on the user.
    """

    list_display = ["email", "full_name", "is_active"]
    list_filter = ["is_active", "assessing_units"]
    list_select_related = ["user"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    filter_horizontal = ["assessing_units"]
    fields = ["email", "first_name", "last_name", "phone_number", "assessing_units", "is_active"]

    def get_readonly_fields(self, request: HttpRequest, obj: Assessor | None = None) -> list[str]:
        """Makes name and email read-only when editing.

        Takes: the request and the assessor being edited (None when adding).
        Returns: the read-only field names (list of str); empty when adding.
        """
        return ["email", "first_name", "last_name"] if obj else []

    def get_form(
        self, request: HttpRequest, obj: Assessor | None = None, change: bool = False, **kwargs: Any
    ) -> type[forms.ModelForm[Assessor]]:
        """Uses the add form (which calls `AssessorService`) only when adding.

        Takes: the request, the assessor being edited (None when adding), and whether
        this is a change.
        Returns: the form class to use.
        """
        if obj is None:
            kwargs["form"] = AssessorAddForm
        return super().get_form(request, obj, change=change, **kwargs)
