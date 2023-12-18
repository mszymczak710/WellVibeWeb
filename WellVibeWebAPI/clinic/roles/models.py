import datetime

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from clinic.auth.models import User
from clinic.dictionaries.models import Specialization
from clinic.models import Address, BaseModel
from clinic.roles.choices import Genre
from clinic.validators import (
    JobExecutionNumberValidator,
    NursingLicenseNumberValidator,
    PeselValidator,
    PhoneNumberValidator,
)


class Doctor(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="doctor",
        verbose_name=_("user"),
    )
    job_execution_number = models.CharField(
        _("job execution number"),
        max_length=7,
        unique=True,
        validators=(JobExecutionNumberValidator,),
    )
    specializations = models.ManyToManyField(
        Specialization,
        related_name="doctors",
        verbose_name=_("specializations"),
    )

    class Meta:
        verbose_name = _("doctor")
        verbose_name_plural = _("doctors")

    def __str__(self):
        return f"{self.user.full_name} ({self.job_execution_number})"


class Nurse(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="nurse",
        verbose_name=_("user"),
    )
    nursing_license_number = models.CharField(
        _("nursing license number"),
        max_length=7,
        unique=True,
        validators=(NursingLicenseNumberValidator,),
    )

    class Meta:
        verbose_name = _("nurse")
        verbose_name_plural = _("nurses")

    def __str__(self):
        return f"{self.user.full_name} ({self.nursing_license_number})"


class Patient(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="patient",
        verbose_name=_("user"),
    )
    pesel = models.CharField(
        _("PESEL"), max_length=11, unique=True, validators=(PeselValidator,)
    )
    phone_number = models.CharField(
        _("phone number"),
        max_length=15,
        validators=(PhoneNumberValidator, MinLengthValidator(7)),
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="patients",
        verbose_name=_("address"),
    )
    doctors = models.ManyToManyField(
        Doctor,
        through="clinic.Visit",
        related_name="patients",
        verbose_name=_("doctors"),
    )

    class Meta:
        verbose_name = _("patient")
        verbose_name_plural = _("patients")

    @property
    def gender(self):
        # Property to determine gender from PESEL
        return Genre.FEMALE if int(self.pesel[9]) % 2 == 0 else Genre.MALE

    @property
    def birth_date(self):
        # Property to determine birth date from PESEL
        year = int(self.pesel[0:2])
        month = int(self.pesel[2:4])
        day = int(self.pesel[4:6])

        if month > 12:
            year += 2000
            month -= 20
        else:
            year += 1900

        return datetime.date(year, month, day)

    def __str__(self):
        return f"{self.user.full_name} ({self.pesel})"
