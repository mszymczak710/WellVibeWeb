import pytest
from rest_framework import status


@pytest.mark.django_db
def test_login_successful(api_client, user):
    login_data = {"email": user.email, "password": "testpassword"}

    response = api_client.post(
        "/auth/login/",
        data=login_data,
        format="json",
    )

    assert (
        response.status_code,
        "access" in response.data,
        "refresh" in response.data,
        response.data["user"]["email"],
        response.data["user"]["first_name"],
        response.data["user"]["last_name"],
    ) == (status.HTTP_200_OK, True, True, "test@example.com", "Test", "User")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_data, expected_status, expected_response",
    (
        (
            {"email": "", "password": "testpassword"},
            status.HTTP_400_BAD_REQUEST,
            {},
        ),
        (
            {"email": "test@example.com", "password": ""},
            status.HTTP_400_BAD_REQUEST,
            {},
        ),
        ({"email": "", "password": ""}, status.HTTP_400_BAD_REQUEST, {}),
        (
            {"email": "test@example.com", "password": "wrongpassword"},
            status.HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid email or password."},
        ),
        ({}, status.HTTP_400_BAD_REQUEST, {}),
    ),
)
def test_login_invalid_input_format(
    api_client, user, input_data, expected_status, expected_response
):
    if "email" in input_data and input_data["email"] == "test@example.com":
        input_data["email"] = user.email

    response = api_client.post("/auth/login/", data=input_data, format="json")

    if expected_response:
        assert (response.status_code, response.data) == (
            expected_status,
            expected_response,
        )
    else:
        assert response.status_code == expected_status


@pytest.mark.django_db
def test_login_nonexistent_user(api_client, user):
    user.email = "nonexistent@example.com"

    login_data = {"email": user.email, "password": "testpassword"}

    response = api_client.post(
        "/auth/login/",
        data=login_data,
        format="json",
    )

    expected_error = "Invalid email or password."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_401_UNAUTHORIZED,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture, expected_detail",
    (
        ("user_not_confirmed", "User is not active."),
        ("inactive_user", "User is not active."),
    ),
)
def test_login_user_status(api_client, request, user_fixture, expected_detail):
    user = request.getfixturevalue(user_fixture)
    login_data = {"email": user.email, "password": "testpassword"}
    response = api_client.post(
        "/auth/login/",
        data=login_data,
        format="json",
    )

    expected_response = {"detail": expected_detail}
    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_multiple_login(api_client, user):
    for _ in range(5):
        response = api_client.post(
            "/auth/login/",
            data={"email": user.email, "password": "testpassword"},
            format="json",
        )

    expected_error = "User is already logged in."
    expected_response = {"error": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("get", "patch", "delete", "put"))
def test_login_user_http_methods_not_allowed(api_client, http_method):
    method = getattr(api_client, http_method)
    response = method("/auth/login/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_data, content_type, expected_status, expected_response",
    (
        (
            "email=test@example.com&password=testpassword",
            "application/x-www-form-urlencoded",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
        (
            "this is not valid json",
            "application/json",
            status.HTTP_400_BAD_REQUEST,
            {
                "detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"
            },
        ),
    ),
)
def test_login_with_invalid_data_format(
    api_client, login_data, content_type, expected_status, expected_response
):
    response = api_client.post(
        "/auth/login/",
        data=login_data,
        content_type=content_type,
    )

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
def test_login_rate_limiting(api_client, user):
    login_data = {"email": user.email, "password": "testpassword"}
    for _ in range(50):
        response = api_client.post(
            "/auth/login/",
            data=login_data,
            format="json",
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
