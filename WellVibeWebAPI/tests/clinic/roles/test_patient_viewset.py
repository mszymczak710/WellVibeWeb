import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", (("patient-list"), ("patient-detail")))
def test_unauthenticated_user_cannot_list_or_retrieve_patients(
    api_client, patient_instances, url_name
):
    patient = patient_instances[0]
    url = reverse(url_name, args=(patient.pk,) if "detail" in url_name else ())
    response = api_client.get(url)

    expected_error = "Authentication credentials were not provided."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_401_UNAUTHORIZED,
        expected_response,
    )


@pytest.mark.django_db
def test_patient_cannot_list_patients(authenticated_patient):
    api_client, _ = authenticated_patient
    url = reverse("patient-list")
    response = api_client.get(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_doctor_or_nurse_can_list_patients(
    api_client, user_fixture, patient_instances, request
):
    url = reverse("patient-list")
    ordering = "readable_id"
    api_client, _ = request.getfixturevalue(user_fixture)
    response = api_client.get(f"{url}?ordering={ordering}")
    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        len(patient_instances),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
@pytest.mark.parametrize(
    "filter_param, filter_value, expected_count",
    (
        ("user__email", "pacjent1@example.com", 1),
        ("user__first_name", "Testowa", 0),
        ("user__last_name", "Patient", 5),
    ),
)
def test_filter_patient(
    filter_param,
    filter_value,
    expected_count,
    api_client,
    user_fixture,
    patient_instances,
    request,
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("patient-list")
    ordering = "readable_id"
    response = api_client.get(
        f"{url}?{filter_param}={filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


@pytest.mark.django_db
def test_patient_can_retrieve_own_details(authenticated_patient):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))
    response = api_client.get(url)

    assert (
        response.status_code,
        response.data["user"]["first_name"],
        response.data["user"]["last_name"],
        response.data["user"]["email"],
        response.data["pesel"],
        response.data["phone_number"],
        response.data["address"]["street"],
        response.data["address"]["house_number"],
        response.data["address"]["city"],
        response.data["address"]["post_code"],
        response.data["address"]["country"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Patient",
        "pacjent1@example.com",
        "99081112341",
        "+48554123651",
        "Inna Ulica",
        "2",
        "Inne Miasto",
        "11-111",
        "Poland",
    )


@pytest.mark.django_db
def test_patient_cannot_retrieve_details_of_another_patient(
    authenticated_patient, patient_instances
):
    api_client, _ = authenticated_patient
    other_patient = patient_instances[1]
    url = reverse("patient-detail", args=(other_patient.pk,))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_doctor_or_nurse_can_retrieve_patient_details(
    api_client, user_fixture, patient_instances, request
):
    patient = patient_instances[0]

    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("patient-detail", args=(patient.pk,))
    response = api_client.get(url)

    assert (
        response.status_code,
        response.data["user"]["first_name"],
        response.data["user"]["last_name"],
        response.data["user"]["email"],
        response.data["pesel"],
        response.data["phone_number"],
        response.data["address"]["street"],
        response.data["address"]["house_number"],
        response.data["address"]["city"],
        response.data["address"]["post_code"],
        response.data["address"]["country"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Patient",
        "pacjent1@example.com",
        "99081112341",
        "+48554123651",
        "Inna Ulica",
        "2",
        "Inne Miasto",
        "11-111",
        "Poland",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_doctor_or_nurse_cannot_retrieve_details_of_nonexistent_patient(
    api_client, user_fixture, random_uuid, request
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("patient-detail", args=(str(random_uuid),))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_delete_method_is_rejected_for_patients(
    user_fixture, request, patient_instances
):
    api_client, _ = request.getfixturevalue(user_fixture)
    patient = patient_instances[0]
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "put"))
def test_patient_unsupported_http_methods_are_rejected_for_patient_details(
    authenticated_patient, http_method
):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    method = getattr(api_client, http_method)
    response = method(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture",
    ("authenticated_doctor", "authenticated_nurse", "authenticated_patient"),
)
def test_post_method_not_supported_for_patients_list(request, user_fixture):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("patient-list")
    patient_data = {
        "user": {
            "email": "nowy_pacjent@example.com",
            "password": "testpassword",
            "first_name": "Nowy",
            "last_name": "Pacjent",
            "role": "P",
        },
        "pesel": "03292845816",
        "phone_number": "+48727516980",
        "address": {
            "street": "Szosa Lubicka",
            "house_number": "21A",
            "apartment_number": "15",
            "city": "Toruń",
            "post_code": "87-100",
            "country": "Poland",
        },
    }

    response = api_client.post(url, patient_data, format="json")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_patient_can_edit_own_data(authenticated_patient, patient_patch_data):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

    patient.refresh_from_db()
    assert (
        response.status_code,
        response.data["phone_number"],
        response.data["address"]["street"],
        response.data["address"]["house_number"],
        response.data["address"]["apartment_number"],
        response.data["address"]["city"],
        response.data["address"]["post_code"],
        response.data["address"]["country"],
    ) == (
        status.HTTP_200_OK,
        "+48727516980",
        "Szosa Lubicka",
        "21A",
        "15",
        "Toruń",
        "87-100",
        "Poland",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value, expected_error, nested_field",
    (
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
def test_patient_cannot_edit_own_data_with_fields_case_insensitive(
    authenticated_patient,
    patient_patch_data,
    field_name,
    field_value,
    expected_error,
    nested_field,
):
    if nested_field:
        patient_patch_data[field_name][nested_field] = field_value
    else:
        patient_patch_data[field_name] = field_value

    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

    if nested_field:
        expected_response = {field_name: {nested_field: [expected_error]}}
    else:
        expected_response = {field_name: [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value, expected_errors, nested_field",
    (
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
def test_patient_cannot_edit_own_data_with_short_fields(
    authenticated_patient,
    patient_patch_data,
    field_name,
    field_value,
    expected_errors,
    nested_field,
):
    if nested_field:
        patient_patch_data[field_name][nested_field] = field_value
    else:
        patient_patch_data[field_name] = field_value

    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

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
    "field_name, base_value, multiplier, expected_errors, nested_field",
    (
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
def test_patient_cannot_edit_own_data_with_long_fields(
    authenticated_patient,
    patient_patch_data,
    field_name,
    base_value,
    multiplier,
    expected_errors,
    nested_field,
):
    if nested_field:
        patient_patch_data[field_name][nested_field] = base_value * multiplier
    else:
        patient_patch_data[field_name] = base_value * multiplier

    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

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
            "phone_number",
            "+48.1234.567",
            [
                "Invalid phone number format. Please enter a valid phone number."
            ],
            None,
        ),
        (
            "address",
            "Testowa6",
            [
                "City name must start with a capital letter and contain only letters, spaces, and dashes."
            ],
            "city",
        ),
        (
            "address",
            "Testowa6",
            [
                "Street name must start with a capital letter and contain only letters, spaces, and dashes."
            ],
            "street",
        ),
        (
            "address",
            "871-00",
            [
                "Invalid postal code format. Please enter a valid postal code in the format XX-XXX."
            ],
            "post_code",
        ),
        (
            "address",
            "Neverland",
            ['"Neverland" is not a valid choice.'],
            "country",
        ),
        (
            "address",
            "15AA",
            [
                "House number must start with a non-zero digit, optionally followed by up to two more digits, and can optionally end with a single letter."
            ],
            "house_number",
        ),
        (
            "address",
            "1A",
            ["Apartment number must be a number between 1 and 999"],
            "apartment_number",
        ),
    ),
)
def test_patient_cannot_edit_own_data_with_invalid_fields(
    authenticated_patient,
    patient_patch_data,
    field_name,
    field_value,
    expected_errors,
    nested_field,
):
    if nested_field:
        patient_patch_data[field_name][nested_field] = field_value
    else:
        patient_patch_data[field_name] = field_value

    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

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
    "patch_data, content_type, format, expected_status, expected_response",
    (
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
            {
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
            "phone_number=123456&address=test",
            "application/x-www-form-urlencoded",
            None,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
    ),
)
def test_patient_cannot_edit_own_data_with_invalid_input_format(
    authenticated_patient,
    patch_data,
    content_type,
    format,
    expected_status,
    expected_response,
):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))
    if not format:
        response = api_client.patch(url, patch_data, content_type=content_type)

    if not content_type:
        response = api_client.patch(url, patch_data, format=format)

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
def test_patient_cannot_edit_read_only_fields(authenticated_patient):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    original_user_email = patient.user.email
    original_user_first_name = patient.user.first_name
    original_user_last_name = patient.user.last_name
    original_user_role = patient.user.role
    original_pesel = patient.pesel

    patch_data = {
        "user": {
            "email": "edytowany_lekarz@example.com",
            "first_name": "Edytowany",
            "last_name": "Lekarz",
            "role": "D",
        },
        "pesel": "03242021457",
    }

    response = api_client.patch(url, patch_data, format="json")

    patient.refresh_from_db()
    assert (
        response.status_code,
        original_pesel,
        original_user_email,
        original_user_first_name,
        original_user_last_name,
        original_user_role,
    ) == (
        status.HTTP_200_OK,
        patient.pesel,
        patient.user.email,
        patient.user.first_name,
        patient.user.last_name,
        patient.user.role,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture",
    ("authenticated_nurse", "authenticated_doctor"),
)
def test_doctor_or_nurse_cannot_edit_patient_data(
    patient_instances, patient_patch_data, request, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    patient = patient_instances[0]

    url = reverse("patient-detail", args=(patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_patient_cannot_edit_other_patient_data(
    authenticated_patient, patient_instances, patient_patch_data
):
    api_client, _ = authenticated_patient
    other_patient = patient_instances[1]

    url = reverse("patient-detail", args=(other_patient.pk,))

    response = api_client.patch(url, data=patient_patch_data, format="json")

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
def test_edit_nonexistent_patient(
    authenticated_patient, patient_patch_data, random_uuid
):
    api_client, _ = authenticated_patient
    url = reverse("patient-detail", args=(str(random_uuid),))

    response = api_client.patch(url, data=patient_patch_data, format="json")

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
def test_patient_cannot_edit_own_data_rate_limiting(
    authenticated_patient, patient_patch_data
):
    api_client, patient = authenticated_patient
    url = reverse("patient-detail", args=(patient.pk,))

    for _ in range(100):
        response = api_client.patch(
            url, data=patient_patch_data, format="json"
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
