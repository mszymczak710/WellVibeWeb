import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status


@pytest.mark.django_db
def test_verify_email_successful(
    api_client, user_not_confirmed, email_verification_url
):
    response = api_client.get(email_verification_url)
    user_not_confirmed.refresh_from_db()

    expected_message = "Email successfully verified."
    expected_response = {"detail": expected_message}

    assert (
        response.status_code,
        user_not_confirmed.email_confirmed,
        user_not_confirmed.is_active,
        response.data,
    ) == (status.HTTP_200_OK, True, True, expected_response)


@pytest.mark.parametrize(
    "uid, token_key, expected_error",
    (
        (
            urlsafe_base64_encode(force_bytes("9999")),
            default_token_generator.make_token,
            "Invalid user.",
        ),
        (
            lambda user: urlsafe_base64_encode(force_bytes(user.pk)),
            "invalidtoken",
            "Token is invalid or expired.",
        ),
    ),
)
@pytest.mark.django_db
def test_verify_email_invalid_args(
    api_client, user_not_confirmed, uid, token_key, expected_error
):
    token = token_key(user_not_confirmed) if callable(token_key) else token_key
    uid = uid(user_not_confirmed) if callable(uid) else uid

    url = reverse("verify-email", args=(uid, token))
    response = api_client.get(url)

    expected_response = {"error": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_verify_email_already_verified(
    api_client, user_not_confirmed, email_verification_url
):
    user_not_confirmed.email_confirmed = True
    user_not_confirmed.save()

    response = api_client.get(email_verification_url)

    expected_error = "Email has already been verified."
    expected_response = {"error": [expected_error]}

    assert (
        response.status_code,
        response.data,
        user_not_confirmed.email_confirmed,
    ) == (status.HTTP_400_BAD_REQUEST, expected_response, True)
    user_not_confirmed.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("post", "patch", "delete", "put"))
def test_verify_email_http_methods_not_allowed(
    api_client, email_verification_url, http_method
):
    method = getattr(api_client, http_method)
    response = method(email_verification_url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
