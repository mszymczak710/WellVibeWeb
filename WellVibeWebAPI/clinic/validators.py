import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

FirstNameValidator = RegexValidator(
    regex=r"^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*(?:[-' ][A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)*$",
    message=_(
        "First name must start with an uppercase letter followed by lowercase letters."
    ),
    code="invalid_first_name",
)

LastNameValidator = RegexValidator(
    regex=r"^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*(?:[-' ][A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)*$",
    message=_(
        "Last name must start with an uppercase letter followed by lowercase letters."
    ),
    code="invalid_last_name",
)

HouseNumberValidator = RegexValidator(
    regex=r"^[1-9]\d{0,2}[A-Za-z]?$",
    message=_(
        "House number must start with a non-zero digit, optionally followed by up to two more digits, and can optionally end with a single letter."
    ),
    code="invalid_house_number",
)

ApartmentNumberValidator = RegexValidator(
    regex=r"^[1-9]\d{0,2}$",
    message=_("Apartment number must be a number between 1 and 999"),
    code="invalid_apartment_number",
)

CityValidator = RegexValidator(
    regex=r"^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż -]*(\s[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż -]*)*$",
    message=_(
        "City name must start with a capital letter and contain only letters, spaces, and dashes."
    ),
    code="invalid_city",
)

StreetValidator = RegexValidator(
    regex=r"^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż -]*(\s[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż -]*)*$",
    message=_(
        "Street name must start with a capital letter and contain only letters, spaces, and dashes."
    ),
    code="invalid_street",
)


PostcodeValidator = RegexValidator(
    regex=r"^\d{2}-\d{3}$",
    message=_(
        "Invalid postal code format. Please enter a valid postal code in the format XX-XXX."
    ),
    code="invalid_post_code",
)


PhoneNumberValidator = RegexValidator(
    regex=r"^\+?(\d{1,3}[-\s]?)?(\(0\d{1,2}\)|0\d{1,2}[-\s]?)?(\d{1,4}[-\s]?){2,3}\d{1,4}$",
    message=_(
        "Invalid phone number format. Please enter a valid phone number."
    ),
    code="invalid_phone_number",
)


def PeselValidator(value):
    if not re.match(r"^\d{11}$", value):
        raise ValidationError(
            _("PESEL number must consist of 11 digits."),
            code="invalid_pesel",
        )

    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    check_sum = sum(w * int(c) for w, c in zip(weights, value)) % 10
    if (10 - check_sum) % 10 != int(value[-1]):
        raise ValidationError(
            _("Invalid PESEL number."),
            code="invalid_pesel",
        )


def JobExecutionNumberValidator(value):
    if not re.match(r"^[1-9]\d{6}$", value):
        raise ValidationError(
            _(
                "Job execution number must consist of 7 digits and cannot start with 0."
            ),
            code="invalid_job_execution_number",
        )

    digits = [int(digit) for digit in value]

    checksum = (
        digits[0] * 1
        + digits[1] * 3
        + digits[2] * 7
        + digits[3] * 9
        + digits[4] * 1
        + digits[5] * 3
        + digits[6] * 7
    ) % 10

    if checksum != 0:
        raise ValidationError(
            _("Invalid job execution number."),
            code="invalid_job_execution_number",
        )


NursingLicenseNumberValidator = RegexValidator(
    regex=r"^[1-9]\d{6}$",
    message=_("The nursing license number must consist of 7 digits."),
    code="invalid_nursing_license_number",
)

PrescriptionCodeValidator = RegexValidator(
    regex=r"^\d{4}$",
    message=_("The prescription code must consist of 4 digits."),
    code="invalid_prescription_code",
)
