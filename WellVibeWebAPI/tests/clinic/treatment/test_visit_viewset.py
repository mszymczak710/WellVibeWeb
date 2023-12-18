import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", (("visit-list"), ("visit-detail")))
def test_unauthenticated_user_cannot_list_or_retrieve_visits(
    api_client, visit_instances, url_name
):
    visit = visit_instances[0]
    url = reverse(url_name, args=(visit.pk,) if "detail" in url_name else ())
    response = api_client.get(url)

    expected_error = "Authentication credentials were not provided."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_401_UNAUTHORIZED,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_doctor"))
)
@pytest.mark.parametrize("http_method", ("delete", "patch"))
def test_patient_or_doctor_invalid_http_methods_are_not_permitted_on_visit_detail(
    request, http_method, visit_instances, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("visit-detail", args=(visit_instances[0].pk,))

    method = getattr(api_client, http_method)
    response = method(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_nurse_can_delete_visit(authenticated_nurse, visit_instances):
    api_client, _ = authenticated_nurse

    url = reverse("visit-detail", args=(visit_instances[0].pk,))
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "get", "patch"))
def test_nurse_cannot_operate_on_nonexistent_visit(
    authenticated_nurse, http_method, request, random_uuid
):
    api_client, _ = authenticated_nurse

    url = reverse("visit-detail", args=(str(random_uuid),))
    method = getattr(api_client, http_method)
    response = method(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture",
    (
        ("authenticated_nurse"),
        ("authenticated_patient"),
        ("authenticated_doctor"),
    ),
)
def test_put_method_are_rejected_on_visit_detail(
    request, visit_instances, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("visit-detail", args=(visit_instances[0].pk,))

    response = api_client.put(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_doctor"))
)
def test_patient_or_doctor_can_list_own_visits(
    request, user_fixture, visit_instances
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("visit-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        2,
    )


@pytest.mark.django_db
def test_nurse_can_list_visits(authenticated_nurse, visit_instances):
    api_client, _ = authenticated_nurse
    url = reverse("visit-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        len(visit_instances),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filter_param, filter_value, expected_count",
    (
        ("visit_status", "I", 1),
        ("patient__pesel", "99081112342", 2),
        ("doctor__job_execution_number", "1000043", 2),
        ("office__office_type__name", "Gabinet medycyny rodzinnej", 2),
        ("office__floor", "0", 1),
        ("is_remote", "False", 4),
        ("disease__name", "Angina", 0),
    ),
)
def test_filter_visit(
    authenticated_nurse,
    filter_param,
    filter_value,
    expected_count,
    visit_instances,
):
    api_client, _ = authenticated_nurse
    url = reverse("visit-list")
    ordering = "readable_id"
    response = api_client.get(
        f"{url}?{filter_param}={filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_filter_param, first_filter_value, second_filter_param, second_filter_value, expected_count",
    (
        (
            "date_after",
            "2023-12-01T10:00:00Z",
            "date_before",
            "2023-12-09T11:00:00Z",
            2,
        ),
        ("duration_in_minutes_min", "20", "duration_in_minutes_max", "35", 3),
    ),
)
def test_double_filter_visit(
    authenticated_nurse,
    first_filter_param,
    first_filter_value,
    second_filter_param,
    second_filter_value,
    expected_count,
    visit_instances,
):
    api_client, _ = authenticated_nurse
    url = reverse("visit-list")
    ordering = "readable_id"
    response = api_client.get(
        f"{url}?{first_filter_param}={first_filter_value}&{second_filter_param}={second_filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_doctor"))
)
def test_patient_or_doctor_can_retrieve_details_of_own_visit(
    request, visit_instances, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    own_visit = visit_instances[0]

    url = reverse("visit-detail", args=(own_visit.pk,))
    response = api_client.get(url)

    response_doctor_data = response.data["doctor"]
    response_office_data = response.data["office"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    assert (
        response.status_code,
        response_doctor_data["user"]["first_name"],
        response_doctor_data["user"]["last_name"],
        response_doctor_data["user"]["email"],
        doctor_specializations,
        response_doctor_data["job_execution_number"],
        response_patient_data["user"]["first_name"],
        response_patient_data["user"]["last_name"],
        response_patient_data["user"]["email"],
        response_patient_data["pesel"],
        response_patient_data["phone_number"],
        response_patient_data["address"]["street"],
        response_patient_data["address"]["house_number"],
        response_patient_data["address"]["city"],
        response_patient_data["address"]["post_code"],
        response_patient_data["address"]["country"],
        response_office_data["office_type"]["name"],
        response_office_data["floor"],
        response.data["date"],
        response.data["duration_in_minutes"],
        response.data["predicted_end_date"],
        response.data["is_remote"],
        response.data["visit_status"],
        response.data["notes"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Doctor",
        "lekarz1@example.com",
        ["Kardiologia"],
        "1000041",
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
        "Gabinet medycyny rodzinnej",
        1,
        "2024-12-01T10:00:00Z",
        20,
        "2024-12-01T10:20:00Z",
        False,
        "S",
        "Visit 1",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_doctor"))
)
def test_patient_or_doctor_cannot_retrieve_details_of_other_visit(
    request, visit_instances, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    other_visit = visit_instances[3]

    url = reverse("visit-detail", args=(other_visit.pk,))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
def test_nurse_can_retrieve_details_of_other_visit(
    authenticated_nurse, visit_instances
):
    api_client, _ = authenticated_nurse
    other_visit = visit_instances[3]

    url = reverse("visit-detail", args=(other_visit.pk,))
    response = api_client.get(url)

    response_doctor_data = response.data["doctor"]
    response_office_data = response.data["office"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    assert (
        response.status_code,
        response_doctor_data["user"]["first_name"],
        response_doctor_data["user"]["last_name"],
        response_doctor_data["user"]["email"],
        doctor_specializations,
        response_doctor_data["job_execution_number"],
        response_patient_data["user"]["first_name"],
        response_patient_data["user"]["last_name"],
        response_patient_data["user"]["email"],
        response_patient_data["pesel"],
        response_patient_data["phone_number"],
        response_patient_data["address"]["street"],
        response_patient_data["address"]["house_number"],
        response_patient_data["address"]["apartment_number"],
        response_patient_data["address"]["city"],
        response_patient_data["address"]["post_code"],
        response_patient_data["address"]["country"],
        response_office_data["office_type"]["name"],
        response_office_data["floor"],
        response.data["date"],
        response.data["duration_in_minutes"],
        response.data["predicted_end_date"],
        response.data["is_remote"],
        response.data["visit_status"],
        response.data["notes"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Doctor",
        "lekarz3@example.com",
        ["Diabetologia"],
        "1000043",
        "Test",
        "Patient",
        "pacjent2@example.com",
        "99081112342",
        "+48554123652",
        "Ulica",
        "1",
        "1A",
        "Miasto",
        "00-000",
        "Poland",
        "Pediatryczny",
        2,
        "2023-12-01T15:45:00Z",
        30,
        "2023-12-01T16:15:00Z",
        True,
        "C",
        "Visit 4",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
def test_nurse_can_create_or_update_visit(
    authenticated_nurse, http_method, api_endpoint, visit_data, visit_instances
):
    api_client, _ = authenticated_nurse
    url = reverse("visit-list")

    if http_method == "patch":
        visit = visit_instances[0]
        url = reverse(api_endpoint, args=(visit.pk,))
        response = api_client.patch(url, data=visit_data, format="json")
        assert response.status_code == status.HTTP_200_OK
    else:
        url = reverse(api_endpoint)
        response = api_client.post(url, data=visit_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    response_doctor_data = response.data["doctor"]
    response_office_data = response.data["office"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    assert (
        response_doctor_data["user"]["first_name"],
        response_doctor_data["user"]["last_name"],
        response_doctor_data["user"]["email"],
        doctor_specializations,
        response_doctor_data["job_execution_number"],
        response_patient_data["user"]["first_name"],
        response_patient_data["user"]["last_name"],
        response_patient_data["user"]["email"],
        response_patient_data["pesel"],
        response_patient_data["phone_number"],
        response_patient_data["address"]["street"],
        response_patient_data["address"]["house_number"],
        response_patient_data["address"]["city"],
        response_patient_data["address"]["post_code"],
        response_patient_data["address"]["country"],
        response_office_data["office_type"]["name"],
        response_office_data["floor"],
        response.data["duration_in_minutes"],
        response.data["is_remote"],
        response.data["visit_status"],
    ) == (
        "Test",
        "Doctor",
        "lekarz1@example.com",
        ["Kardiologia"],
        "1000041",
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
        "Gabinet medycyny rodzinnej",
        1,
        30,
        False,
        "S",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_doctor"))
)
def test_patient_or_doctor_cannot_create_visit(
    user_fixture, visit_data, request
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("visit-list")

    response = api_client.post(url, data=visit_data, format="json")

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize("duration_in_minutes", (5, 200))
def test_nurse_cannot_create_or_update_visit_with_invalid_duration(
    authenticated_nurse,
    http_method,
    api_endpoint,
    duration_in_minutes,
    visit_instances,
    visit_data,
):
    api_client, _ = authenticated_nurse

    if http_method == "patch":
        visit = visit_instances[0]
        patched_data = {"duration_in_minutes": duration_in_minutes}
        url = reverse(api_endpoint, args=(visit.pk,))
        response = api_client.patch(url, data=patched_data, format="json")
    else:
        visit_data["duration_in_minutes"] = duration_in_minutes
        url = reverse(api_endpoint)
        response = api_client.post(url, data=visit_data, format="json")

    expected_error = (
        "Duration of the visit must be between 10 and 180 minutes."
    )
    expected_response = {"duration_in_minutes": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize(
    "date",
    (
        datetime.now(timezone.utc) - timedelta(days=1),
        datetime.now(timezone.utc),
    ),
)
def test_nurse_cannot_create_or_update_visit_with_invalid_date(
    authenticated_nurse,
    http_method,
    api_endpoint,
    date,
    visit_instances,
    visit_data,
):
    api_client, _ = authenticated_nurse

    if http_method == "patch":
        visit = visit_instances[0]
        patched_data = {"date": date.isoformat()}
        url = reverse(api_endpoint, args=(visit.pk,))
        response = api_client.patch(url, data=patched_data, format="json")
    else:
        visit_data["date"] = date.isoformat()
        url = reverse(api_endpoint)
        response = api_client.post(url, data=visit_data, format="json")

    expected_error = "Date must be in the future."
    expected_response = {"date": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize(
    "data, content_type, format, expected_status, expected_response",
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
                "date": "",
                "duration_in_minutes": "",
                "doctor": "",
                "patient": "",
                "office": "",
            },
            None,
            "json",
            status.HTTP_400_BAD_REQUEST,
            {
                "date": [
                    "Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ],
                "duration_in_minutes": ["A valid integer is required."],
                "doctor": ["This field may not be null."],
                "patient": ["This field may not be null."],
                "office": ["This field may not be null."],
            },
        ),
        (
            "date=2023-12-13T15:45:00Z&duration_in_minutes=4&doctor=1&office=3&patient=2",
            "application/x-www-form-urlencoded",
            None,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
    ),
)
def test_nurse_cannot_create_or_update_visit_with_invalid_input_format(
    authenticated_nurse,
    http_method,
    api_endpoint,
    data,
    content_type,
    format,
    expected_status,
    expected_response,
    visit_instances,
):
    api_client, _ = authenticated_nurse
    visit = visit_instances[0]

    if http_method == "post":
        url = reverse(api_endpoint)
        response = api_client.post(
            url, data=data, content_type=content_type, format=format
        )
    elif http_method == "patch":
        url = reverse(api_endpoint, args=(visit.pk,))
        if (
            isinstance(data, str)
            and content_type == "application/x-www-form-urlencoded"
        ):
            data_dict = dict(parse_qsl(data))
            response = api_client.patch(
                url, data=data_dict, content_type=content_type
            )
        else:
            response = api_client.patch(
                url, data=data, content_type=content_type, format=format
            )

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize(
    "field_name, field_value",
    (
        ("doctor", uuid.uuid4()),
        ("patient", uuid.uuid4()),
        ("office", uuid.uuid4()),
        ("disease", uuid.uuid4()),
    ),
)
def test_nurse_cannot_create_or_update_visit_with_nonexistent_entities(
    authenticated_nurse,
    api_endpoint,
    http_method,
    field_name,
    field_value,
    visit_data,
    visit_instances,
):
    api_client, _ = authenticated_nurse
    visit_data[field_name] = field_value

    if http_method == "post":
        url = reverse(api_endpoint)
        response = api_client.post(url, data=visit_data, format="json")
    elif http_method == "patch":
        visit = visit_instances[0]
        url = reverse(api_endpoint, args=(visit.pk,))
        response = api_client.patch(url, data=visit_data, format="json")

    expected_error = f'Invalid pk "{field_value}" - object does not exist.'
    expected_response = {field_name: [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize("overlap_field", ("doctor", "office", "patient"))
def test_visit_overlap_validation(
    authenticated_nurse,
    doctor_instances,
    office_instances,
    patient_instances,
    visit_data,
    overlap_field,
    api_endpoint,
    http_method,
    visit_instances,
):
    api_client, _ = authenticated_nurse

    visit_date = datetime.fromisoformat(visit_data["date"])

    overlapping_visit_data = {
        "date": visit_date - timedelta(minutes=15),
        "duration_in_minutes": 30,
        "doctor": visit_data["doctor"]
        if overlap_field == "doctor"
        else doctor_instances[1].pk,
        "office": visit_data["office"]
        if overlap_field == "office"
        else office_instances[1].pk,
        "patient": visit_data["patient"]
        if overlap_field == "patient"
        else patient_instances[1].pk,
    }

    api_client.post(reverse("visit-list"), data=visit_data, format="json")

    if http_method == "post":
        url = reverse(api_endpoint)
        response = api_client.post(
            url, data=overlapping_visit_data, format="json"
        )
    elif http_method == "patch":
        visit = visit_instances[0]
        url = reverse(api_endpoint, args=[visit.pk])
        response = api_client.patch(
            url, data=overlapping_visit_data, format="json"
        )

    if overlap_field == "office":
        expected_error = f"{overlap_field.capitalize()} is not available during the selected time."
    else:
        expected_error = (
            f"{overlap_field.capitalize()} has an overlapping visit."
        )

    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("index", (1, 2))
def test_nurse_cannot_update_visit_if_visit_status_is_completed_or_in_progress(
    authenticated_nurse, index, visit_data, visit_instances
):
    api_client, _ = authenticated_nurse
    visit = visit_instances[index]
    url = reverse("visit-detail", args=(visit.pk,))
    response = api_client.patch(url, data=visit_data, format="json")

    expected_error = "Cannot modify a visit that is in progress or completed."
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_nurse_cannot_update_visit_if_visit_is_scheduled_for_tomorrow(
    authenticated_nurse, visit_data, visit_instances
):
    api_client, _ = authenticated_nurse
    visit = visit_instances[4]
    url = reverse("visit-detail", args=(visit.pk,))
    response = api_client.patch(url, data=visit_data, format="json")

    expected_error = (
        "Cannot modify the visit within 24 hours of its scheduled start."
    )
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method, api_endpoint",
    (("post", "visit-list"), ("patch", "visit-detail")),
)
@pytest.mark.parametrize(
    "value, multiplier, expected_error",
    (("long", 150, ["Ensure this field has no more than 500 characters."]),),
)
def test_nurse_cannot_create_or_update_visit_with_too_long_notes(
    authenticated_nurse,
    http_method,
    api_endpoint,
    value,
    multiplier,
    expected_error,
    visit_instances,
    visit_data,
):
    api_client, _ = authenticated_nurse

    if http_method == "patch":
        visit = visit_instances[0]
        patched_data = {"notes": value * multiplier}
        url = reverse(api_endpoint, args=(visit.pk,))
        response = api_client.patch(url, data=patched_data, format="json")
    else:
        visit_data["notes"] = value * multiplier
        url = reverse(api_endpoint)
        response = api_client.post(url, data=visit_data, format="json")

    expected_response = {"notes": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_nurse_cannot_create_visit_with_rate_limiting(
    authenticated_nurse, visit_data
):
    api_client, _ = authenticated_nurse
    url = reverse("visit-list")

    for _ in range(60):
        response = api_client.post(url, data=visit_data, format="json")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_nurse_cannot_update_visit_with_rate_limiting(
    authenticated_nurse, visit_data, visit_instances
):
    api_client, _ = authenticated_nurse
    url = reverse("visit-detail", args=(visit_instances[0].pk,))

    for _ in range(60):
        response = api_client.patch(url, data=visit_data, format="json")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
