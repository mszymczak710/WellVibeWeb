from django.utils.translation import gettext_lazy as _
from django_countries.serializer_fields import CountryField
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from clinic.roles.models import Address


class AddressSerializer(CountryFieldMixin, serializers.ModelSerializer):
    country = CountryField(label=_("Country"), name_only=True)

    class Meta:
        model = Address
        fields = (
            "country",
            "street",
            "house_number",
            "apartment_number",
            "city",
            "post_code",
        )
