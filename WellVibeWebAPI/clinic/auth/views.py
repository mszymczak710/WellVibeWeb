import logging
from datetime import datetime, timezone

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from clinic.auth.models import User
from clinic.auth.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    LogoutSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordSerializer,
    UserLoginSerializer,
    UserReadSerializer,
    UserRegisterSerializer,
)
from clinic.mixins import MailSendingMixin

logger = logging.getLogger(__name__)


class RegisterView(MailSendingMixin, APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer
    throttle_classes = (AnonRateThrottle,)

    @extend_schema(
        request=UserRegisterSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "string"},
                        "access": {"type": "string"},
                    },
                },
            )
        },
    )
    def post(self, request):
        """
        Handle POST request for user registration.

        Validates user data, creates a new user, sends verification email, and issues JWT tokens.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Send email verification link if the user's email is not confirmed
        if not user.email_confirmed:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = request.build_absolute_uri(
                reverse("verify-email", args=(uidb64, token))
            )
            self.send_email(
                subject=_("[WellVibeWeb] Verify your email"),
                template_name="emails/email_verification.html",
                context={"user": user, "verification_link": verification_link},
                to_email=user.email,
            )

        # Generate JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        response_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailVerificationSerializer

    @extend_schema(
        request=EmailVerificationSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Email successfully verified.",
            )
        },
    )
    def get(self, request, uidb64, token):
        """
        Handle GET request for email verification.

        Args:
            request: The original HTTP request.
            uidb64 (str): The base64 encoded ID of the user to verify.
            token (str): The token to validate the user's email verification request.

        Returns:
            Response: A DRF Response object with the verification result.
        """
        # Deserialize the input data and validate
        serializer = self.serializer_class(
            data={"uidb64": uidb64, "token": token}
        )
        serializer.is_valid(raise_exception=True)

        # Retrieve the user from the validated data
        user = serializer.validated_data["user"]

        # Confirm the user's email and activate their account
        user.email_confirmed = True
        user.is_active = True
        user.save()

        # Return a success response message
        return Response(
            {"detail": _("Email successfully verified.")},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer
    throttle_classes = (AnonRateThrottle,)

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "string"},
                        "access": {"type": "string"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "first_name": {"type": "string"},
                                "last_name": {"type": "string"},
                            },
                        },
                    },
                }
            )
        },
    )
    def post(self, request):
        """
        Handle POST request for user login.

        Args:
            request: The HttpRequest object containing the login credentials.

        Returns:
            Response: The DRF Response object with JWT tokens and user data.
        """
        # Authenticate user credentials
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate(username=email, password=password)

        # Set login flag
        user.is_logged_in = True
        user.save()

        # Generate JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        user_serializer = UserReadSerializer(user)

        # Prepare the response data
        response_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user_serializer.data,
        }

        # Return the access and refresh tokens along with user information
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer
    throttle_classes = (UserRateThrottle,)

    @extend_schema(
        request=LogoutSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request):
        """
        Handle POST request for user logout.

        Args:
            request: The HttpRequest object containing the refresh token.

        Returns:
            Response: The DRF Response object with HTTP 204 status indicating no content.
        """
        # Validate refresh token and retrieve user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh_token = serializer.validated_data["refresh"]

        # Set logout flag
        user.is_logged_in = False
        user.save()

        # Invalidate the refresh token
        token = RefreshToken(refresh_token)
        token.set_jti()
        token.set_exp()

        # Return HTTP 204 No Content, indicating logout was successful
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(MailSendingMixin, APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer
    throttle_classes = (AnonRateThrottle,)

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Password reset link has been sent if the account exists.",
            )
        },
    )
    def post(self, request):
        """
        Sends a password reset link to the user's email if the account exists.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Create reset password link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_password_url = request.build_absolute_uri(
            reverse("reset-password-confirm", args=(uid, token))
        )

        # Send reset password email
        self.send_email(
            subject=_("[WellVibeWeb] Reset password"),
            template_name="emails/reset_password.html",
            context={"reset_password_url": reset_password_url},
            to_email=user.email,
        )

        # Record the time when the reset password email was sent
        user.password_reset_sent_at = datetime.now(timezone.utc)
        user.save()

        # Respond indicating the reset link has been sent
        return Response(
            {
                "detail": _(
                    "Password reset link has been sent if the account exists."
                )
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordConfirmView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordConfirmSerializer
    throttle_classes = (AnonRateThrottle,)

    @extend_schema(
        request=ResetPasswordConfirmSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Password has been reset with the new password.",
            )
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Resets the user's password with the new password provided.
        """
        try:
            # Decode UID from base64 and retrieve the user
            uid = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
            token = kwargs["token"]

            # Validate the token and new password
            serializer = self.serializer_class(
                data=request.data,
                context={
                    "user": user,
                    "token": token,
                    "uidb64": kwargs["uidb64"],
                },
            )

            serializer.is_valid(raise_exception=True)

            # Set the new password for the user and save
            user.set_password(serializer.validated_data["password"])
            user.save()

            # Respond indicating the password has been reset
            return Response(
                {
                    "detail": _(
                        "Password has been reset with the new password."
                    )
                },
                status=status.HTTP_200_OK,
            )

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # Respond with an error if the UID is invalid or the user does not exist
            return Response(
                {"error": _("Invalid UID or user not found.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    throttle_classes = (UserRateThrottle,)

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Password updated successfully",
            )
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Handles the POST request to change the user's password.

        Args:
            request: The HttpRequest object containing the old and new passwords.

        Returns:
            Response: A Response object with a success message and HTTP 200 status if the password is updated successfully.
        """
        # Validate and process the password change
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        # Update to the new password
        new_password = serializer.validated_data["password"]
        request.user.set_password(new_password)
        request.user.save()

        # Return a success response message
        return Response(
            {"detail": _("Password updated successfully")},
            status=status.HTTP_200_OK,
        )
