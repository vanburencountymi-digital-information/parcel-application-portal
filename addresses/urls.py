from django.urls import path

from . import views

app_name = "addresses"

urlpatterns = [
    path("", views.home, name="home"),
    path("address/", views.address_form_view, name="address-form"),
]
