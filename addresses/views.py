from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import AddressForm
from .services.address_service import AddressService
from .services.exceptions import AddressVerificationError


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "addresses/home.html")


def address_form_view(request: HttpRequest) -> HttpResponse:
    result = None
    error = None

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            try:
                result = AddressService().verify(address)
            except AddressVerificationError as exc:
                error = str(exc)
    else:
        form = AddressForm()

    return render(
        request,
        "addresses/address_form.html",
        {"form": form, "result": result, "error": error},
    )
