import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_doctor_can_list_specializations(
    authenticated_doctor, specialization_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("specialization-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        3,
    )


@pytest.mark.django_db
def test_filter_specialization_by_name(
    authenticated_doctor, specialization_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("specialization-list")
    search_query = "Diabetologia"
    ordering = "readable_id"
    response = api_client.get(f"{url}?name={search_query}&ordering={ordering}")

    assert (
        response.status_code,
        len(response.data["results"]),
        response.data["results"][0]["name"],
    ) == (status.HTTP_200_OK, 1, "Diabetologia")


@pytest.mark.django_db
def test_doctor_can_retrieve_specific_specialization_details(
    authenticated_doctor, specialization_instances
):
    api_client, _ = authenticated_doctor
    url = reverse(
        "specialization-detail", args=(specialization_instances[0].pk,)
    )
    response = api_client.get(url)
    assert (response.status_code, response.data["name"]) == (
        status.HTTP_200_OK,
        "Kardiologia",
    )


@pytest.mark.django_db
def test_doctor_cannot_retrieve_details_of_nonexistent_specialization(
    authenticated_doctor, random_uuid
):
    api_client, _ = authenticated_doctor
    url = reverse("specialization-detail", args=(str(random_uuid),))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", (("specialization-list"), ("specialization-detail"))
)
def test_unauthenticated_user_cannot_list_or_retrieve_specializations(
    api_client, specialization_instances, url_name
):
    specialization = specialization_instances[0]
    url = reverse(
        url_name, args=(specialization.pk,) if "detail" in url_name else ()
    )
    response = api_client.get(url)

    expected_error = "Authentication credentials were not provided."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_401_UNAUTHORIZED,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture", (("authenticated_patient"), ("authenticated_nurse"))
)
@pytest.mark.parametrize(
    "url_name", (("specialization-list"), ("specialization-detail"))
)
def test_user_with_invalid_role_cannot_list_or_retrieve_specializations(
    request, user_fixture, url_name, specialization_instances
):
    api_client, _ = request.getfixturevalue(user_fixture)
    specialization = specialization_instances[0]
    url = reverse(
        url_name, args=(specialization.pk,) if "detail" in url_name else ()
    )
    response = api_client.get(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "patch", "put"))
def test_invalid_http_methods_are_rejected_on_specialization_detail(
    authenticated_doctor, http_method, specialization_instances
):
    api_client, _ = authenticated_doctor
    url = reverse(
        "specialization-detail", args=(specialization_instances[0].pk,)
    )

    method = getattr(api_client, http_method)
    response = method(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_post_method_not_supported_for_specializations_list(
    authenticated_doctor,
):
    api_client, _ = authenticated_doctor
    url = reverse("specialization-list")
    specialization_data = {
        "name": "Testowa specjalizacja",
    }

    response = api_client.post(url, specialization_data, format="json")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
