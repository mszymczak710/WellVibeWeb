import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_doctor_can_list_diseases(authenticated_doctor, disease_instances):
    api_client, _ = authenticated_doctor
    url = reverse("disease-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        3,
    )


@pytest.mark.django_db
def test_filter_disease_by_name(authenticated_doctor, disease_instances):
    api_client, _ = authenticated_doctor
    url = reverse("disease-list")
    ordering = "readable_id"
    search_query = "Depresja"
    response = api_client.get(f"{url}?name={search_query}&ordering={ordering}")

    assert (
        response.status_code,
        len(response.data["results"]),
        response.data["results"][0]["name"],
    ) == (status.HTTP_200_OK, 1, "Depresja")


@pytest.mark.django_db
def test_doctor_can_retrieve_specific_disease_details(
    authenticated_doctor, disease_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("disease-detail", args=(disease_instances[0].pk,))
    response = api_client.get(url)
    assert (response.status_code, response.data["name"]) == (
        status.HTTP_200_OK,
        "Depresja",
    )


@pytest.mark.django_db
def test_doctor_cannot_retrieve_details_of_nonexistent_disease(
    authenticated_doctor, random_uuid
):
    api_client, _ = authenticated_doctor
    url = reverse("disease-detail", args=(str(random_uuid),))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", (("disease-list"), ("disease-detail")))
def test_unauthenticated_user_cannot_list_or_retrieve_diseases(
    api_client, disease_instances, url_name
):
    disease = disease_instances[0]
    url = reverse(url_name, args=(disease.pk,) if "detail" in url_name else ())
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
@pytest.mark.parametrize("url_name", (("disease-list"), ("disease-detail")))
def test_user_with_invalid_role_cannot_list_or_retrieve_diseases(
    request, user_fixture, url_name, disease_instances
):
    api_client, _ = request.getfixturevalue(user_fixture)
    disease = disease_instances[0]
    url = reverse(url_name, args=(disease.pk,) if "detail" in url_name else ())
    response = api_client.get(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "patch", "put"))
def test_invalid_http_methods_are_rejected_on_disease_detail(
    authenticated_doctor, http_method, disease_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("disease-detail", args=(disease_instances[0].pk,))

    method = getattr(api_client, http_method)
    response = method(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_post_method_not_supported_for_diseases_list(authenticated_doctor):
    api_client, _ = authenticated_doctor
    url = reverse("disease-list")
    disease_data = {
        "name": "Testowa choroba",
    }

    response = api_client.post(url, disease_data, format="json")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
