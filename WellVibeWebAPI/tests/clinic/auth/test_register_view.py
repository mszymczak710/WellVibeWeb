import pytest
from rest_framework import status

from clinic.auth.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "send_email_called",
    (False, True),
)
def test_register_user_successful(
    api_client,
    mocker,
    user_data,
    send_email_called,
):
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    if send_email_called:
        mocked_send_email = mocker.patch(
            "clinic.mixins.MailSendingMixin.send_email"
        )

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    assert (
        response.status_code,
        "refresh" in response.data,
        "access" in response.data,
    ) == (status.HTTP_201_CREATED, True, True)

    if send_email_called:
        mocked_send_email.assert_called_once()


@pytest.mark.django_db
def test_register_user_bad_request(api_client, mocker, user_data):
    user_data.pop("email", None)
    user_data.pop("last_name", None)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_register_user_existing_email(api_client, mocker, user_data):
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)
    User.objects.create_user(
        email="existing@example.com",
        password="existingpassword",
        first_name="Jan",
        last_name="Testowy",
    )

    user_data["email"] = "existing@example.com"

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )
    expected_error = "This email address is already in use."
    expected_response = {"email": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value, patch_return, expected_errors, nested_field",
    (
        (
            "first_name",
            "./Test123./",
            True,
            [
                "First name must start with an uppercase letter followed by lowercase letters."
            ],
            None,
        ),
        (
            "last_name",
            "<Test123>",
            True,
            [
                "Last name must start with an uppercase letter followed by lowercase letters."
            ],
            None,
        ),
        (
            "email",
            "invalidemail",
            True,
            ["Enter a valid email address."],
            None,
        ),
        (
            "role",
            "INVALID_ROLE",
            True,
            ['"INVALID_ROLE" is not a valid choice.'],
            None,
        ),
        (
            "recaptcha_response",
            None,
            False,
            ["Invalid reCAPTCHA. Please try again."],
            None,
        ),
        (
            "pesel",
            "1234A5B123C",
            True,
            ["PESEL number must consist of 11 digits."],
            None,
        ),
        (
            "pesel",
            "12345678901",
            True,
            ["Invalid PESEL number."],
            None,
        ),
        (
            "phone_number",
            "+48.1234.567",
            True,
            [
                "Invalid phone number format. Please enter a valid phone number."
            ],
            None,
        ),
        (
            "address",
            "Testowa6",
            True,
            [
                "City name must start with a capital letter and contain only letters, spaces, and dashes."
            ],
            "city",
        ),
        (
            "address",
            "Testowa6",
            True,
            [
                "Street name must start with a capital letter and contain only letters, spaces, and dashes."
            ],
            "street",
        ),
        (
            "address",
            "871-00",
            True,
            [
                "Invalid postal code format. Please enter a valid postal code in the format XX-XXX."
            ],
            "post_code",
        ),
        (
            "address",
            "Neverland",
            True,
            ['"Neverland" is not a valid choice.'],
            "country",
        ),
        (
            "address",
            "15AA",
            True,
            [
                "House number must start with a non-zero digit, optionally followed by up to two more digits, and can optionally end with a single letter."
            ],
            "house_number",
        ),
        (
            "address",
            "1A",
            True,
            ["Apartment number must be a number between 1 and 999"],
            "apartment_number",
        ),
    ),
)
def test_register_user_invalid_fields(
    api_client,
    mocker,
    user_data,
    field_name,
    field_value,
    patch_return,
    expected_errors,
    nested_field,
):
    if nested_field:
        user_data[field_name][nested_field] = field_value
    elif field_value is not None:
        user_data[field_name] = field_value

    mocker.patch(
        "clinic.auth.serializers.verify_recaptcha", return_value=patch_return
    )

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    if nested_field:
        expected_response = {field_name: {nested_field: expected_errors}}
    else:
        expected_response = {field_name: expected_errors}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password, password_confirm, expected_response",
    (
        (
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
            "password123",
            "password123",
            {"password": ["This password is too common."]},
        ),
        (
            "validpassword123",
            "differentpassword123",
            {"password": ["Passwords must match."]},
        ),
    ),
)
def test_register_user_password_validation(
    api_client,
    mocker,
    user_data,
    password,
    password_confirm,
    expected_response,
):
    user_data["password"] = password
    user_data["password_confirm"] = password_confirm
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing_fields, expected_response",
    (
        (
            ["password", "password_confirm"],
            {
                "password": ["This field is required."],
                "password_confirm": ["This field is required."],
            },
        ),
        (
            ["password_confirm"],
            {"password_confirm": ["This field is required."]},
        ),
        (
            ["recaptcha_response"],
            {"recaptcha_response": ["This field is required."]},
        ),
    ),
)
def test_register_user_missing_password_or_recaptcha_fields(
    api_client, mocker, user_data, missing_fields, expected_response
):
    for field in missing_fields:
        user_data.pop(field, None)
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, base_value, multiplier, expected_errors, nested_field",
    (
        (
            "first_name",
            "Longtest",
            10,
            [
                "First name must start with an uppercase letter followed by lowercase letters.",
                "Ensure this field has no more than 30 characters.",
            ],
            None,
        ),
        (
            "last_name",
            "Longuser",
            10,
            [
                "Last name must start with an uppercase letter followed by lowercase letters.",
                "Ensure this field has no more than 30 characters.",
            ],
            None,
        ),
        (
            "email",
            "long" * 65 + "@example.com",
            1,
            ["Ensure this field has no more than 255 characters."],
            None,
        ),
        (
            "pesel",
            "12345",
            4,
            [
                "PESEL number must consist of 11 digits.",
                "Ensure this field has no more than 11 characters.",
            ],
            None,
        ),
        (
            "phone_number",
            "12345",
            4,
            [
                "Invalid phone number format. Please enter a valid phone number.",
                "Ensure this field has no more than 15 characters.",
            ],
            None,
        ),
        (
            "address",
            "Test" + "test" * 15,
            1,
            ["Ensure this field has no more than 50 characters."],
            "city",
        ),
        (
            "address",
            "Test" + "test" * 15,
            1,
            ["Ensure this field has no more than 50 characters."],
            "street",
        ),
    ),
)
def test_register_user_with_long_fields(
    api_client,
    mocker,
    user_data,
    field_name,
    base_value,
    multiplier,
    expected_errors,
    nested_field,
):
    if nested_field:
        user_data[field_name][nested_field] = base_value * multiplier
    else:
        user_data[field_name] = base_value * multiplier

    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    if nested_field:
        expected_response = {field_name: {nested_field: expected_errors}}
    else:
        expected_response = {field_name: expected_errors}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value, expected_errors, nested_field",
    (
        (
            "first_name",
            "A",
            ["Ensure this field has at least 3 characters."],
            None,
        ),
        (
            "last_name",
            "A",
            ["Ensure this field has at least 2 characters."],
            None,
        ),
        (
            "email",
            "a@bc.d",
            [
                "Ensure this field has at least 7 characters.",
                "Enter a valid email address.",
            ],
            None,
        ),
        ("pesel", "12345", ["PESEL number must consist of 11 digits."], None),
        (
            "phone_number",
            "12345",
            ["Ensure this field has at least 7 characters."],
            None,
        ),
        (
            "address",
            "A",
            ["Ensure this field has at least 3 characters."],
            "city",
        ),
        (
            "address",
            "A",
            ["Ensure this field has at least 3 characters."],
            "street",
        ),
    ),
)
def test_register_user_with_short_fields(
    api_client,
    mocker,
    user_data,
    field_name,
    field_value,
    expected_errors,
    nested_field,
):
    if nested_field:
        user_data[field_name][nested_field] = field_value
    else:
        user_data[field_name] = field_value

    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    if nested_field:
        expected_response = {field_name: {nested_field: expected_errors}}
    else:
        expected_response = {field_name: expected_errors}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value, expected_error, nested_field",
    (
        (
            "first_name",
            "test",
            "First name must start with an uppercase letter followed by lowercase letters.",
            None,
        ),
        (
            "last_name",
            "user",
            "Last name must start with an uppercase letter followed by lowercase letters.",
            None,
        ),
        (
            "address",
            "test",
            "City name must start with a capital letter and contain only letters, spaces, and dashes.",
            "city",
        ),
        (
            "address",
            "test",
            "Street name must start with a capital letter and contain only letters, spaces, and dashes.",
            "street",
        ),
    ),
)
def test_register_user_fields_case_insensitive(
    api_client,
    mocker,
    user_data,
    field_name,
    field_value,
    expected_error,
    nested_field,
):
    if nested_field:
        user_data[field_name][nested_field] = field_value
    else:
        user_data[field_name] = field_value

    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    if nested_field:
        expected_response = {field_name: {nested_field: [expected_error]}}
    else:
        expected_response = {field_name: [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_register_user_email_case_insensitive(api_client, mocker, user_data):
    User.objects.create_user(
        email="test@example.com",
        password="somepassword",
        first_name="Sensitive",
        last_name="Email",
    )

    user_data["email"] = "TEST@example.com"
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)

    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    expected_error = "This email address is already in use."
    expected_response = {"email": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_data, content_type, format, expected_status, expected_response",
    (
        (
            {},
            None,
            "json",
            status.HTTP_400_BAD_REQUEST,
            {
                "email": ["This field is required."],
                "first_name": ["This field is required."],
                "last_name": ["This field is required."],
                "role": ["This field is required."],
                "password": ["This field is required."],
                "password_confirm": ["This field is required."],
                "recaptcha_response": ["This field is required."],
                "pesel": ["This field is required."],
                "phone_number": ["This field is required."],
                "address": ["This field is required."],
            },
        ),
        (
            {
                "first_name": "",
                "last_name": "",
                "email": "",
                "role": "",
                "password": "",
                "password_confirm": "",
                "recaptcha_response": "",
                "pesel": "",
                "phone_number": "",
                "address": {
                    "city": "",
                    "street": "",
                    "country": "",
                    "house_number": "",
                    "post_code": "",
                },
            },
            None,
            "json",
            status.HTTP_400_BAD_REQUEST,
            {
                "email": ["This field may not be blank."],
                "first_name": ["This field may not be blank."],
                "last_name": ["This field may not be blank."],
                "role": ['"" is not a valid choice.'],
                "password": ["This field may not be blank."],
                "password_confirm": ["This field may not be blank."],
                "recaptcha_response": ["This field may not be blank."],
                "pesel": ["This field may not be blank."],
                "phone_number": ["This field may not be blank."],
                "address": {
                    "city": ["This field may not be blank."],
                    "street": ["This field may not be blank."],
                    "country": ['"" is not a valid choice.'],
                    "house_number": ["This field may not be blank."],
                    "post_code": ["This field may not be blank."],
                },
            },
        ),
        (
            "this is not valid json",
            "application/json",
            None,
            status.HTTP_400_BAD_REQUEST,
            {
                "detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"
            },
        ),
        (
            "first_name=Test&last_name=User&email=test@example.com&password=testpassword&password_confirm=testpassword",
            "application/x-www-form-urlencoded",
            None,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
    ),
)
def test_register_user_invalid_input_format(
    api_client,
    input_data,
    content_type,
    format,
    expected_status,
    expected_response,
):
    if not format:
        response = api_client.post(
            "/auth/register/", data=input_data, content_type=content_type
        )

    if not content_type:
        response = api_client.post(
            "/auth/register/", data=input_data, format=format
        )

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
def test_register_user_while_logged_in(api_client, mocker, user_data):
    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)
    registration_response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )
    assert registration_response.status_code == status.HTTP_201_CREATED

    user = User.objects.get(email=user_data["email"])

    api_client.force_authenticate(user=user)

    mocker.patch("clinic.auth.serializers.verify_recaptcha", return_value=True)
    response = api_client.post(
        "/auth/register/", data=user_data, format="json"
    )

    expected_response = {
        "email": ["This email address is already in use."],
        "pesel": [
            "The information provided is incomplete or incorrect. Please check and re-enter your details."
        ],
    }

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("get", "patch", "delete", "put"))
def test_register_user_http_methods_not_allowed(api_client, http_method):
    method = getattr(api_client, http_method)
    response = method("/auth/register/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_register_user_rate_limiting(api_client, user_data):
    for _ in range(50):
        response = api_client.post(
            "/auth/register/", data=user_data, format="json"
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
