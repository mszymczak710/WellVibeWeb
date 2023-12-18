import pytest
from rest_framework import status


@pytest.mark.django_db
def test_change_password_successful(
    authenticated_client, user, change_password_data
):
    user.set_password(change_password_data["old_password"])
    user.save()
    response = authenticated_client.post(
        "/auth/change-password/", data=change_password_data, format="json"
    )
    user.refresh_from_db()
    password = change_password_data["password"]
    assert (response.status_code, user.check_password(password)) == (
        status.HTTP_200_OK,
        True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "old_password, password, password_confirm, expected_response",
    (
        (
            "testpassword",
            "short",
            "short",
            {
                "password": [
                    "This password is too short. It must contain at least 8 characters.",
                    "Ensure this field has at least 8 characters.",
                ],
                "password_confirm": [
                    "Ensure this field has at least 8 characters."
                ],
            },
        ),
        (
            "testpassword",
            "password123",
            "password123",
            {"password": ["This password is too common."]},
        ),
        (
            "testpassword",
            "validpassword123",
            "mismatchedpassword",
            {"password": ["Passwords must match."]},
        ),
        (
            "wrongpassword",
            "newpassword123",
            "newpassword123",
            {"old_password": ["Wrong password."]},
        ),
    ),
)
def test_change_password_validations(
    authenticated_client,
    user,
    old_password,
    password,
    password_confirm,
    expected_response,
):
    setup_password = "testpassword"
    user.set_password(setup_password)
    user.save()

    change_password_data = {
        "old_password": old_password,
        "password": password,
        "password_confirm": password_confirm,
    }

    response = authenticated_client.post(
        "/auth/change-password/", data=change_password_data, format="json"
    )

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("get", "patch", "delete", "put"))
def test_change_password_http_methods_not_allowed(
    authenticated_client, http_method
):
    method = getattr(authenticated_client, http_method)
    response = method("/auth/change-password/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_data, content_type, expected_status, expected_response",
    (
        (
            "this is not valid json",
            "application/json",
            status.HTTP_400_BAD_REQUEST,
            {
                "detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"
            },
        ),
        (
            "old_password=testpassword&password=testpassword123&password_confirm=testpassword123",
            "application/x-www-form-urlencoded",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
        (
            {},
            "application/json",
            status.HTTP_400_BAD_REQUEST,
            {
                "old_password": ["This field is required."],
                "password": ["This field is required."],
                "password_confirm": ["This field is required."],
            },
        ),
    ),
)
def test_change_password_data_format(
    authenticated_client,
    input_data,
    content_type,
    expected_status,
    expected_response,
):
    response = authenticated_client.post(
        "/auth/change-password/",
        data=input_data,
        content_type=content_type,
    )

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_field, update_data, expected_response",
    (
        ("password", {}, {"password": ["This field is required."]}),
        (
            "old_password",
            {"password": "newpassword", "password_confirm": "newpassword"},
            {
                "old_password": ["This field is required."],
                "password": ["This password is too common."],
            },
        ),
    ),
)
def test_change_password_missing_data(
    authenticated_client,
    change_password_data,
    missing_field,
    update_data,
    expected_response,
):
    change_password_data.pop(missing_field, None)

    change_password_data.update(update_data)

    response = authenticated_client.post(
        "/auth/change-password/", data=change_password_data, format="json"
    )

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_change_password_unauthorized_access(api_client, change_password_data):
    response = api_client.post(
        "/auth/change-password/", data=change_password_data, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_change_password_rate_limiting(
    authenticated_client, user, change_password_data
):
    user.set_password(change_password_data["old_password"])
    user.save()

    for _ in range(50):
        response = authenticated_client.post(
            "/auth/change-password/", data=change_password_data, format="json"
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
