from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from clinic.auth.choices import Role
from clinic.auth.recaptcha import verify_recaptcha
from clinic.roles.models import Patient
from clinic.serializers import AddressSerializer
from clinic.validators import PeselValidator, PhoneNumberValidator

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")
        read_only_fields = fields  # All fields are read-only


class UserWriteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        min_length=7,
        max_length=255,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This email address is already in use."),
                lookup="iexact",
            )
        ],
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class PasswordBaseSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=(validate_password,),
    )
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """
        Validate that the password and password_confirm fields match.

        Args:
            data (dict): The input data for the serializer.

        Returns:
            dict: The validated data, excluding password_confirm.

        Raises:
            ValidationError: If the passwords do not match.
        """
        # Check if the passwords match
        password = data.get("password")
        password_confirm = data.get("password_confirm")
        if password != password_confirm:
            raise serializers.ValidationError(
                {"password": _("Passwords must match.")}
            )

        # Remove password_confirm from the validated data since it's no longer needed
        data.pop("password_confirm", None)

        return data


class UserRegisterSerializer(
    UserWriteSerializer, PasswordBaseSerializer, serializers.ModelSerializer
):
    recaptcha_response = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Role.choices)
    pesel = serializers.CharField(max_length=11, validators=(PeselValidator,))
    phone_number = serializers.CharField(
        min_length=7, max_length=15, validators=(PhoneNumberValidator,)
    )
    address = AddressSerializer()

    class Meta(UserWriteSerializer.Meta):
        fields = UserWriteSerializer.Meta.fields + (
            "password",
            "password_confirm",
            "recaptcha_response",
            "role",
            "pesel",
            "phone_number",
            "address",
        )

    def validate_recaptcha_response(self, value):
        """Validate the reCAPTCHA response."""
        if not verify_recaptcha(value):
            raise serializers.ValidationError(
                _("Invalid reCAPTCHA. Please try again.")
            )
        return value

    def validate_pesel(self, value):
        """Validate the PESEL number especially for patient role."""
        role = self.initial_data.get("role")

        # Ensure PESEL is unique for patients
        if (
            role == Role.PATIENT
            and Patient.objects.filter(pesel=value).exists()
        ):
            raise serializers.ValidationError(
                _(
                    "The information provided is incomplete or incorrect. Please check and re-enter your details."
                )
            )
        return value

    def validate(self, data):
        """
        Perform object-level validation on user registration data.
        """
        # Ensure authenticated users cannot re-register
        request = self.context["request"]
        if request.user.is_authenticated:
            raise serializers.ValidationError(
                _("You are already registered and logged in.")
            )

        return super().validate(data)

    def create(self, validated_data):
        """
        Create a new user instance with the provided validated data.
        """
        # Extract password fields and reCAPTCHA response which are not part of the User model
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)
        validated_data.pop("recaptcha_response", None)

        # Extract additional registration fields
        pesel = validated_data.pop("pesel", None)
        phone_number = validated_data.pop("phone_number", None)
        address_data = validated_data.pop("address", None)
        role = validated_data.get("role")

        # Auto-confirm admin, doctor, and nurse accounts
        if role in (Role.ADMIN, Role.DOCTOR, Role.NURSE):
            validated_data["email_confirmed"] = True
            validated_data["is_active"] = True

        # Create the user object
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Handle patient-specific data
        if role == Role.PATIENT:
            address = (
                self.create_address(address_data) if address_data else None
            )
            Patient.objects.create(
                user=user,
                pesel=pesel,
                phone_number=phone_number,
                address=address,
            )

        return user

    def create_address(self, address_data):
        """
        Helper method to create an address instance from the provided data.
        """
        # Validate and save the address using AddressSerializer
        address_serializer = AddressSerializer(data=address_data)
        address_serializer.is_valid(raise_exception=True)
        return address_serializer.save()


class EmailVerificationSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate the UID and token for email verification.
        """
        uidb64 = attrs.get("uidb64")
        token = attrs.get("token")

        try:
            # Decode the base64 user ID and retrieve the corresponding user.
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # If the user ID is not found, raise a validation error.
            raise serializers.ValidationError({"error": _("Invalid user.")})

        if user.email_confirmed:
            # If the user's email is already verified, raise an error.
            raise serializers.ValidationError(
                {"error": _("Email has already been verified.")}
            )

        if not default_token_generator.check_token(user, token):
            # If the token is invalid or expired, raise an error.
            raise serializers.ValidationError(
                {"error": _("Token is invalid or expired.")}
            )

        # If all checks pass, include the user instance in the validated data.
        attrs["user"] = user
        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Check email and password and validate the user's login request.
        """
        # Attempt to retrieve the user by email
        user = User.objects.filter(email=data["email"]).first()

        # Check for invalid credentials
        if not user or not user.check_password(data["password"]):
            raise AuthenticationFailed(_("Invalid email or password."))

        # Check if the user is already logged in
        if user.is_logged_in:
            raise serializers.ValidationError(
                {"error": _("User is already logged in.")}
            )

        # Check for inactive or unconfirmed email
        if not user.is_active or not user.email_confirmed:
            raise PermissionDenied(_("User is not active."))

        # All checks passed, return the validated data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        """
        Validate the refresh token and retrieve the associated user.
        """
        # Retrieve the refresh token from the data
        refresh = data.get("refresh")

        # Ensure the refresh token is provided
        if not refresh:
            raise serializers.ValidationError(
                {"error": _("Refresh token is required.")}
            )

        try:
            # Decode the refresh token to get the user ID
            token = RefreshToken(refresh)
            user_id = token.payload.get("user_id", None)
            # Ensure the token contains a user ID
            if not user_id:
                raise serializers.ValidationError(
                    {
                        "error": _(
                            "Token is invalid or does not have a user_id."
                        )
                    }
                )

            # Retrieve the user associated with the user ID
            user = User.objects.get(id=user_id)
        except TokenError:
            # The token is invalid or expired
            raise serializers.ValidationError(
                {"error": _("Token is invalid or expired.")}
            )
        except User.DoesNotExist:
            # No user was found matching this token's user ID
            raise serializers.ValidationError(
                {"error": _("User does not exist.")}
            )

        # Include the user in the validated data
        data["user"] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    recaptcha_response = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validate the email and ensure the associated user has confirmed their email.
        """
        # Retrieve the user based on the email provided
        user = User.objects.filter(email=data["email"]).first()

        # If no user is found with that email, raise an error
        if not user:
            raise serializers.ValidationError(
                {"error": _("Invalid email address.")}
            )

        # If the user's email hasn't been confirmed, raise a permission error
        if not user.email_confirmed:
            raise PermissionDenied(
                _(
                    "To reset your password, please first confirm your email address."
                )
            )

        # Include the user instance in the validated data for further processing
        data["user"] = user
        return data

    def validate_recaptcha_response(self, value):
        """
        Validate the reCAPTCHA response.
        """
        # Use the verify_recaptcha utility to check the reCAPTCHA response
        if not verify_recaptcha(value):
            raise serializers.ValidationError(
                _("Invalid reCAPTCHA. Please try again.")
            )

        # If the reCAPTCHA is valid, return the value
        return value


class ResetPasswordConfirmSerializer(PasswordBaseSerializer):
    def validate(self, data):
        data = super().validate(data)

        # Retrieve the user and token from the serializer's context
        user = self.context.get("user")
        token = self.context.get("token")

        # Validate the presence of a user and token
        if not user:
            raise serializers.ValidationError(
                {"error": _("Invalid UID or user not found.")}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "error": _(
                        "User is inactive. Contact support for assistance."
                    )
                }
            )
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {
                    "error": _(
                        "The reset password link is invalid or has expired. Please request a new one."
                    )
                }
            )

        # Check if the password reset link has expired
        if user.password_reset_sent_at:
            time_since_reset = (
                datetime.now(timezone.utc) - user.password_reset_sent_at
            )
            if time_since_reset > timedelta(hours=24):
                raise serializers.ValidationError(
                    {
                        "error": _(
                            "The reset password link has expired. Please request a new one."
                        )
                    }
                )

        return data


class ChangePasswordSerializer(PasswordBaseSerializer, serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        # Check the provided old password against the user's current password
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Wrong password."))
        return value
