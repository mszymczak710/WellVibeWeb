import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", (("nurse-list"), ("nurse-detail")))
def test_unauthenticated_user_cannot_list_or_retrieve_nurses(
    api_client, nurse_instances, url_name
):
    nurse = nurse_instances[0]
    url = reverse(url_name, args=(nurse.pk,) if "detail" in url_name else ())
    response = api_client.get(url)

    expected_error = "Authentication credentials were not provided."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_401_UNAUTHORIZED,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_nurse", "authenticated_patient")
)
def test_user_with_invalid_role_cannot_list_nurses(
    api_client, user_fixture, request
):
    url = reverse("nurse-list")
    api_client, _ = request.getfixturevalue(user_fixture)
    response = api_client.get(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_can_list_nurses(authenticated_doctor, nurse_instances):
    api_client, _ = authenticated_doctor
    url = reverse("nurse-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        len(nurse_instances),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filter_param, filter_value, expected_count",
    (
        ("nursing_license_number", "1234569", 1),
        ("user__email", "pielegniarka1@example.com", 1),
        ("user__first_name", "Testowa", 0),
        ("user__last_name", "Nurse", 3),
    ),
)
def test_filter_nurse(
    authenticated_doctor,
    filter_param,
    filter_value,
    expected_count,
    nurse_instances,
):
    api_client, _ = authenticated_doctor
    url = reverse("nurse-list")
    ordering = "readable_id"
    response = api_client.get(
        f"{url}?{filter_param}={filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


@pytest.mark.django_db
def test_patient_cannot_retrieve_nurse_details(
    authenticated_patient, nurse_instances
):
    api_client, _ = authenticated_patient
    nurse = nurse_instances[0]
    url = reverse("nurse-detail", args=(nurse.pk,))
    response = api_client.get(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_retrieve_details_of_nonexistent_nurse(
    authenticated_doctor, random_uuid
):
    api_client, _ = authenticated_doctor
    url = reverse("nurse-detail", args=(str(random_uuid),))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_can_retrieve_nurse_details(
    authenticated_doctor, nurse_instances
):
    api_client, _ = authenticated_doctor
    nurse = nurse_instances[0]
    url = reverse("nurse-detail", args=(nurse.pk,))
    response = api_client.get(url)
    assert (
        response.status_code,
        response.data["user"]["first_name"],
        response.data["user"]["last_name"],
        response.data["user"]["email"],
        response.data["nursing_license_number"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Nurse",
        "pielegniarka1@example.com",
        "1234568",
    )


@pytest.mark.django_db
def test_nurse_can_retrieve_own_details(authenticated_nurse, nurse_instances):
    api_client, nurse = authenticated_nurse
    url = reverse("nurse-detail", args=(nurse.pk,))
    response = api_client.get(url)

    assert (
        response.status_code,
        response.data["user"]["first_name"],
        response.data["user"]["last_name"],
        response.data["user"]["email"],
        response.data["nursing_license_number"],
    ) == (
        status.HTTP_200_OK,
        "Test",
        "Nurse",
        "pielegniarka1@example.com",
        "1234568",
    )


@pytest.mark.django_db
def test_nurse_cannot_retrieve_details_of_another_nurse(
    authenticated_nurse, nurse_instances
):
    api_client, _ = authenticated_nurse
    other_nurse = nurse_instances[1]
    url = reverse("nurse-detail", args=(other_nurse.pk,))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "patch", "put"))
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_unsupported_http_methods_are_rejected_for_nurse_detail(
    request, nurse_instances, http_method, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    nurse = nurse_instances[0]
    url = reverse("nurse-detail", args=(nurse.pk,))

    method = getattr(api_client, http_method)
    response = method(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", ("authenticated_doctor", "authenticated_nurse")
)
def test_post_method_not_supported_for_nurses_list(request, user_fixture):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("nurse-list")
    nurse_data = {
        "user": {
            "email": "nowa_pielegniarka@example.com",
            "password": "testpassword",
            "first_name": "Nowa",
            "last_name": "Pielęgniarka",
            "role": "N",
        },
        "nursing_license_number": "1234567",
    }

    response = api_client.post(url, nurse_data, format="json")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
