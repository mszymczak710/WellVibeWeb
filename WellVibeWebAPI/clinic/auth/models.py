from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from clinic.auth.choices import Role
from clinic.validators import FirstNameValidator, LastNameValidator


class UserManager(BaseUserManager):
    def _create_user(
        self, email, first_name, last_name, password, **extra_fields
    ):
        """
        Create and return a user with the given email, first name, last name, and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email, first_name, last_name, password=None, **extra_fields
    ):
        extra_fields.setdefault("role", Role.PATIENT)
        return self._create_user(
            email, first_name, last_name, password, **extra_fields
        )

    def create_superuser(
        self, email, first_name, last_name, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        return self._create_user(
            email, first_name, last_name, password, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        _("email address"),
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(7)],
    )
    email_confirmed = models.BooleanField(_("email confirmed"), default=False)
    first_name = models.CharField(
        _("first name"),
        max_length=30,
        validators=[FirstNameValidator, MinLengthValidator(3)],
    )
    last_name = models.CharField(
        _("last name"),
        max_length=30,
        validators=[LastNameValidator, MinLengthValidator(2)],
    )
    register_date = models.DateTimeField(_("register date"), auto_now_add=True)
    is_active = models.BooleanField(_("is active"), default=False)
    is_logged_in = models.BooleanField(
        _("is logged in"),
        default=False,
    )
    is_staff = models.BooleanField(_("is staff"), default=False)
    is_superuser = models.BooleanField(_("is superuser"), default=False)
    password_reset_sent_at = models.DateTimeField(
        _("password reset sent at"), null=True
    )
    role = models.CharField(
        _("role"), max_length=1, choices=Role.choices, default=Role.PATIENT
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} ({self.email})"
