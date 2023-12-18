import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_logout_successful(authenticated_client, user):
    refresh = RefreshToken.for_user(user)

    logout_data = {"refresh": str(refresh)}

    response = authenticated_client.post(
        "/auth/logout/", data=logout_data, format="json"
    )
    user.refresh_from_db()
    assert (response.status_code, user.is_logged_in) == (
        status.HTTP_204_NO_CONTENT,
        False,
    )


@pytest.mark.django_db
def test_logout_unauthorized_access(api_client, user):
    refresh = RefreshToken.for_user(user)

    logout_data = {"refresh": str(refresh)}

    response = api_client.post(
        "/auth/logout/", data=logout_data, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "refresh_token_data, content_type, expected_status, expected_response",
    (
        (
            None,
            "application/json",
            status.HTTP_400_BAD_REQUEST,
            {"error": ["Refresh token is required."]},
        ),
        (
            {"refresh": "invalidRefreshToken"},
            "application/json",
            status.HTTP_400_BAD_REQUEST,
            None,
        ),
        (
            "refresh=refreshToken",
            "application/x-www-form-urlencoded",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
    ),
)
def test_logout_errors(
    authenticated_client,
    refresh_token_data,
    content_type,
    expected_status,
    expected_response,
):
    if isinstance(refresh_token_data, dict):
        response = authenticated_client.post(
            "/auth/logout/", data=refresh_token_data, format="json"
        )
    else:
        response = authenticated_client.post(
            "/auth/logout/",
            data=refresh_token_data,
            content_type=content_type,
        )

    if expected_response:
        assert (response.data, response.status_code) == (
            expected_response,
            expected_status,
        )
    else:
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("get", "patch", "delete", "put"))
def test_logout_user_http_methods_not_allowed(
    authenticated_client, http_method
):
    method = getattr(authenticated_client, http_method)
    response = method("/auth/logout/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_logout_rate_limiting(authenticated_client, user):
    refresh = RefreshToken.for_user(user)

    logout_data = {"refresh": str(refresh)}

    for _ in range(50):
        response = authenticated_client.post(
            "/auth/logout/", data=logout_data, format="json"
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
