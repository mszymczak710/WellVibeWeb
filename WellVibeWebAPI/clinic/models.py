import uuid

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

# Assuming that clinic.auth.models.User and clinic.fields.AutoIncrementField are correctly implemented elsewhere
from clinic.auth.models import User  # noqa: F401
from clinic.fields import AutoIncrementField
from clinic.validators import (
    ApartmentNumberValidator,
    CityValidator,
    HouseNumberValidator,
    PostcodeValidator,
    StreetValidator,
)


class BaseModel(models.Model):
    """
    An abstract base model that provides an ID and a human-readable ID to other models.

    The ID is a UUID field, ensuring a unique identifier across different instances.
    The readable_id is an auto-incrementing field, providing a user-friendly unique number.
    """

    id = models.UUIDField(
        _("id"), primary_key=True, default=uuid.uuid4
    )  # Universally unique identifier
    readable_id = AutoIncrementField(
        _("readable id"), unique=True
    )  # User-friendly unique identifier

    class Meta:
        abstract = True  # Indicates that this model will not be used to create any database table


class Address(models.Model):
    street = models.CharField(
        _("street"),
        max_length=50,
        validators=(StreetValidator, MinLengthValidator(3)),
    )
    house_number = models.CharField(
        _("house number"), max_length=4, validators=(HouseNumberValidator,)
    )
    apartment_number = models.CharField(
        _("apartment number"),
        max_length=4,
        blank=True,
        null=True,
        validators=(ApartmentNumberValidator,),
    )
    city = models.CharField(
        _("city"),
        max_length=50,
        validators=(CityValidator, MinLengthValidator(3)),
    )
    post_code = models.CharField(
        _("post code"), max_length=6, validators=(PostcodeValidator,)
    )
    country = CountryField(
        _("country"), blank_label=_("Country")
    )  # Uses a specialized CountryField for country selection

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    def __str__(self):
        country_name = self.country.name if self.country else ""
        address = f"ul. {self.street} {self.house_number}"

        if self.apartment_number:
            address += f"/{self.apartment_number}"
        address += f", {self.post_code} {self.city}, {country_name}"
        return address
