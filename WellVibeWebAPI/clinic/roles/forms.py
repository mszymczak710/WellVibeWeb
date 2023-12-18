from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from clinic.roles.models import Address, Patient
from clinic.validators import (
    ApartmentNumberValidator,
    CityValidator,
    HouseNumberValidator,
    PostcodeValidator,
    StreetValidator,
)


class PatientAddressAdminForm(forms.ModelForm):
    """
    A ModelForm for the Patient model to include address fields with custom validation.

    This form adds fields for street, house number, apartment number, city, post code,
    and country. It uses custom validators to ensure the data integrity for addresses.
    """

    street = forms.CharField(
        min_length=3,
        max_length=50,
        validators=(StreetValidator,),
        label=_("Street"),
    )
    house_number = forms.CharField(
        max_length=4,
        validators=(HouseNumberValidator,),
        label=_("House number"),
    )
    apartment_number = forms.CharField(
        max_length=4,
        required=False,
        validators=(ApartmentNumberValidator,),
        label=_("Apartment number"),
    )
    city = forms.CharField(
        min_length=3,
        max_length=50,
        validators=(CityValidator,),
        label=_("City"),
    )
    post_code = forms.CharField(
        max_length=6,
        validators=(PostcodeValidator,),
        label=_("Post code"),
    )
    country = CountryField(_("country")).formfield(
        widget=CountrySelectWidget()
    )

    class Meta:
        model = Patient
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """
        Initialize the form instance, setting initial values for address fields
        if the Patient instance has an associated address.
        """
        super().__init__(*args, **kwargs)

        # Initialize form fields with instance's address if available
        if hasattr(self.instance, "address"):
            self.fields["street"].initial = self.instance.address.street
            self.fields[
                "house_number"
            ].initial = self.instance.address.house_number
            self.fields[
                "apartment_number"
            ].initial = self.instance.address.apartment_number
            self.fields["city"].initial = self.instance.address.city
            self.fields["post_code"].initial = self.instance.address.post_code
            self.fields["country"].initial = self.instance.address.country

    def save(self, commit=True):
        """
        Save the form, creating or updating the associated Address instance
        before saving the Patient instance.
        """
        # Process and save the address, then save the Patient instance
        address_data = {
            "street": self.cleaned_data.get("street"),
            "house_number": self.cleaned_data.get("house_number"),
            "apartment_number": self.cleaned_data.get("apartment_number"),
            "city": self.cleaned_data.get("city"),
            "post_code": self.cleaned_data.get("post_code"),
            "country": self.cleaned_data.get("country"),
        }
        address = Address(**address_data)
        address.save()

        patient = super().save(commit=False)
        patient.address = address
        if commit:
            patient.save()
        return patient
