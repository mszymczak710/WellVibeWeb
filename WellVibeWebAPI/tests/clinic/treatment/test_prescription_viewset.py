import uuid

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", (("prescription-list"), ("prescription-detail"))
)
def test_unauthenticated_user_cannot_list_or_retrieve_prescriptions(
    api_client, prescription_instances, url_name
):
    prescription = prescription_instances[0]
    url = reverse(
        url_name, args=(prescription.pk,) if "detail" in url_name else ()
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
def test_patient_or_nurse_cannot_delete_prescription(
    request, prescription_instances, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("prescription-detail", args=(prescription_instances[0].pk,))

    response = api_client.delete(url)

    expected_error = "You do not have permission to perform this action."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_403_FORBIDDEN,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_can_delete_prescription(
    authenticated_doctor, prescription_instances
):
    api_client, _ = authenticated_doctor

    url = reverse("prescription-detail", args=(prescription_instances[0].pk,))
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.parametrize("http_method", ("delete", "get"))
def test_doctor_cannot_operate_on_nonexistent_prescription(
    authenticated_doctor, http_method, random_uuid
):
    api_client, _ = authenticated_doctor

    url = reverse("prescription-detail", args=(str(random_uuid),))
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
@pytest.mark.parametrize("http_method", ("put", "patch"))
def test_put_and_patch_methods_are_rejected_on_prescription_detail(
    request, prescription_instances, http_method, user_fixture
):
    api_client, _ = request.getfixturevalue(user_fixture)
    url = reverse("prescription-detail", args=(prescription_instances[0].pk,))

    method = getattr(api_client, http_method)
    response = method(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_doctor_can_list_prescriptions(
    authenticated_doctor, prescription_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        len(prescription_instances),
    )


@pytest.mark.django_db
def test_patient_can_list_own_prescriptions(
    authenticated_patient, prescription_instances
):
    api_client, _ = authenticated_patient
    url = reverse("prescription-list")
    ordering = "readable_id"
    response = api_client.get(f"{url}?ordering={ordering}")

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        2,
    )


@pytest.mark.django_db
def test_patient_cannot_retrieve_details_of_other_prescription(
    authenticated_patient, prescription_instances
):
    api_client, _ = authenticated_patient
    other_prescription = prescription_instances[3]

    url = reverse("prescription-detail", args=(other_prescription.pk,))
    response = api_client.get(url)

    expected_error = "Not found."
    expected_response = {"detail": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_404_NOT_FOUND,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filter_param, filter_value, expected_count",
    (
        ("patient__pesel", "99081112342", 1),
        ("doctor__job_execution_number", "1000043", 1),
        ("medicine", "Euthyrox", 1),
    ),
)
def test_filter_prescription(
    authenticated_doctor,
    filter_param,
    filter_value,
    expected_count,
    prescription_instances,
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")
    ordering = "readable_id"
    response = api_client.get(
        f"{url}?{filter_param}={filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


def test_filter_prescription_by_visit(
    authenticated_doctor, visit_instances, prescription_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")
    ordering = "readable_id"

    filter_param = "visit"
    filter_value = visit_instances[0].pk
    expected_count = 0

    response = api_client.get(
        f"{url}?{filter_param}={filter_value}&ordering={ordering}"
    )

    assert (response.status_code, len(response.data["results"])) == (
        status.HTTP_200_OK,
        expected_count,
    )


@pytest.mark.django_db
def test_patient_can_retrieve_details_of_own_prescription(
    authenticated_patient, prescription_instances
):
    api_client, _ = authenticated_patient
    own_prescription = prescription_instances[0]

    url = reverse("prescription-detail", args=(own_prescription.pk,))
    response = api_client.get(url)

    response_doctor_data = response.data["doctor"]
    response_dosages_data = response.data["dosages"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    dosages = [
        {
            "medicine_name": dosage["medicine"]["name"],
            "type_of_medicine": dosage["medicine"]["type_of_medicine"]["name"],
            "active_ingredients": [
                {
                    "name": ingredient["ingredient"]["name"],
                    "quantity": ingredient["quantity"],
                    "unit": ingredient["unit"],
                }
                for ingredient in dosage["medicine"]["active_ingredients"]
            ],
            "amount": dosage["amount"],
            "form": dosage["form"]["name"],
            "frequency": dosage["frequency"],
        }
        for dosage in response_dosages_data
    ]

    expected_dosages = [
        {
            "medicine_name": "Euthyrox",
            "type_of_medicine": "Lek na niedoczynność tarczycy",
            "active_ingredients": [
                {
                    "name": "Lewotyroksyna sodowa",
                    "quantity": "100.000",
                    "unit": "mcg",
                }
            ],
            "amount": "1.00",
            "form": "Tabletka",
            "frequency": "1 raz dziennie",
        }
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
        dosages,
        response.data["prescription_code"],
        response.data["description"],
        response.data["visit"],
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
        expected_dosages,
        "1234",
        "Test prescription 1",
        None,
    )


@pytest.mark.django_db
def test_doctor_can_retrieve_details_of_other_prescription(
    authenticated_doctor, prescription_instances, visit_instances
):
    api_client, _ = authenticated_doctor
    other_prescription = prescription_instances[3]

    url = reverse("prescription-detail", args=(other_prescription.pk,))
    response = api_client.get(url)

    response_doctor_data = response.data["doctor"]
    response_dosages_data = response.data["dosages"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    dosages = [
        {
            "medicine_name": dosage["medicine"]["name"],
            "type_of_medicine": dosage["medicine"]["type_of_medicine"]["name"],
            "active_ingredients": [
                {
                    "name": ingredient["ingredient"]["name"],
                    "quantity": ingredient["quantity"],
                    "unit": ingredient["unit"],
                }
                for ingredient in dosage["medicine"]["active_ingredients"]
            ],
            "amount": dosage["amount"],
            "form": dosage["form"]["name"],
            "frequency": dosage["frequency"],
        }
        for dosage in response_dosages_data
    ]

    expected_dosages = [
        {
            "medicine_name": "Ibuprofen Kids",
            "type_of_medicine": "Lek przeciwzapalny niesteroidowy",
            "active_ingredients": [
                {"name": "Ibuprofen", "quantity": "100.000", "unit": "mg/ml"}
            ],
            "amount": "1.50",
            "form": "Syrop",
            "frequency": "2 razy dziennie",
        }
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
        dosages,
        response.data["prescription_code"],
        response.data["description"],
        response.data["visit"],
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
        expected_dosages,
        "1237",
        "Test prescription 4",
        visit_instances[3].pk,
    )


@pytest.mark.django_db
def test_doctor_can_create_prescription(
    authenticated_doctor, prescription_data
):
    api_client, _ = authenticated_doctor

    url = reverse("prescription-list")
    response = api_client.post(url, data=prescription_data, format="json")

    response_doctor_data = response.data["doctor"]
    response_dosages_data = response.data["dosages"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    dosages = [
        {
            "medicine_name": dosage["medicine"]["name"],
            "type_of_medicine": dosage["medicine"]["type_of_medicine"]["name"],
            "active_ingredients": [
                {
                    "name": ingredient["ingredient"]["name"],
                    "quantity": ingredient["quantity"],
                    "unit": ingredient["unit"],
                }
                for ingredient in dosage["medicine"]["active_ingredients"]
            ],
            "amount": dosage["amount"],
            "form": dosage["form"]["name"],
            "frequency": dosage["frequency"],
        }
        for dosage in response_dosages_data
    ]

    expected_dosages = [
        {
            "medicine_name": "Euthyrox",
            "type_of_medicine": "Lek na niedoczynność tarczycy",
            "active_ingredients": [
                {
                    "name": "Lewotyroksyna sodowa",
                    "quantity": "100.000",
                    "unit": "mcg",
                }
            ],
            "amount": "1.50",
            "form": "Tabletka",
            "frequency": "rano",
        }
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
        dosages,
        response.data["prescription_code"],
        response.data["description"],
        response.data["visit"],
    ) == (
        status.HTTP_201_CREATED,
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
        expected_dosages,
        "3333",
        "Description",
        None,
    )


@pytest.mark.django_db
def test_doctor_can_create_prescription_with_visit_data(
    authenticated_doctor, prescription_data_with_visit, visit_instances
):
    api_client, _ = authenticated_doctor

    url = reverse("prescription-list")
    response = api_client.post(
        url, data=prescription_data_with_visit, format="json"
    )

    response_doctor_data = response.data["doctor"]
    response_dosages_data = response.data["dosages"]
    response_patient_data = response.data["patient"]

    doctor_specializations = [
        specialization["name"]
        for specialization in response_doctor_data["specializations"]
    ]

    dosages = [
        {
            "medicine_name": dosage["medicine"]["name"],
            "type_of_medicine": dosage["medicine"]["type_of_medicine"]["name"],
            "active_ingredients": [
                {
                    "name": ingredient["ingredient"]["name"],
                    "quantity": ingredient["quantity"],
                    "unit": ingredient["unit"],
                }
                for ingredient in dosage["medicine"]["active_ingredients"]
            ],
            "amount": dosage["amount"],
            "form": dosage["form"]["name"],
            "frequency": dosage["frequency"],
        }
        for dosage in response_dosages_data
    ]

    expected_dosages = [
        {
            "medicine_name": "Euthyrox",
            "type_of_medicine": "Lek na niedoczynność tarczycy",
            "active_ingredients": [
                {
                    "name": "Lewotyroksyna sodowa",
                    "quantity": "100.000",
                    "unit": "mcg",
                }
            ],
            "amount": "1.50",
            "form": "Tabletka",
            "frequency": "rano",
        }
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
        dosages,
        response.data["prescription_code"],
        response.data["description"],
        response.data["visit"],
    ) == (
        status.HTTP_201_CREATED,
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
        expected_dosages,
        "3333",
        "Description",
        visit_instances[0].pk,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, field_value",
    (("doctor", uuid.uuid4()), ("patient", uuid.uuid4())),
)
def test_doctor_cannot_create_prescription_with_nonexistent_entities(
    authenticated_doctor, field_name, field_value, prescription_data
):
    api_client, _ = authenticated_doctor
    prescription_data[field_name] = field_value

    url = reverse("prescription-list")
    response = api_client.post(url, data=prescription_data, format="json")

    expected_error = f'Invalid pk "{field_value}" - object does not exist.'
    expected_response = {field_name: [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_create_prescription_with_nonexistent_visit(
    authenticated_doctor, prescription_data
):
    api_client, _ = authenticated_doctor
    visit = uuid.uuid4()
    prescription_data["visit"] = visit

    url = reverse("prescription-list")
    response = api_client.post(url, data=prescription_data, format="json")

    expected_error = f'Invalid pk "{visit}" - object does not exist.'
    expected_response = {"visit": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
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
                "doctor": None,
                "patient": None,
                "visit": None,
                "prescription_code": "",
                "description": "",
                "dosages": [
                    {
                        "medicine": None,
                        "amount": "",
                        "frequency": "",
                    }
                ],
            },
            None,
            "json",
            status.HTTP_400_BAD_REQUEST,
            {
                "dosages": [
                    {
                        "medicine": ["This field may not be null."],
                        "amount": ["A valid number is required."],
                        "frequency": ["This field may not be blank."],
                    }
                ],
                "prescription_code": ["This field may not be blank."],
                "description": ["This field may not be blank."],
            },
        ),
        (
            "&doctor=1&patient=2&prescription_code=1234&description=Test",
            "application/x-www-form-urlencoded",
            None,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": 'Unsupported media type "application/x-www-form-urlencoded" in request.'
            },
        ),
    ),
)
def test_doctor_cannot_create_prescription_with_invalid_input_format(
    authenticated_doctor,
    data,
    content_type,
    format,
    expected_status,
    expected_response,
):
    api_client, _ = authenticated_doctor

    url = reverse("prescription-list")
    response = api_client.post(
        url, data, content_type=content_type, format=format
    )

    assert (response.status_code, response.data) == (
        expected_status,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_fixture",
    (
        pytest.lazy_fixture("prescription_data"),
        pytest.lazy_fixture("prescription_data_with_visit"),
    ),
)
@pytest.mark.parametrize(
    "value, multiplier, expected_error",
    (("long", 150, ["Ensure this field has no more than 500 characters."]),),
)
def test_doctor_cannot_create_prescription_with_too_long_description(
    authenticated_doctor, data_fixture, value, multiplier, expected_error
):
    api_client, _ = authenticated_doctor

    data_fixture["description"] = value * multiplier
    url = reverse("prescription-list")
    response = api_client.post(url, data=data_fixture, format="json")

    expected_response = {"description": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_fixture",
    (
        pytest.lazy_fixture("prescription_data"),
        pytest.lazy_fixture("prescription_data_with_visit"),
    ),
)
@pytest.mark.parametrize(
    "code, expected_error",
    (
        ("text", ["The prescription code must consist of 4 digits."]),
        ("123", ["The prescription code must consist of 4 digits."]),
        (
            "14543",
            [
                "The prescription code must consist of 4 digits.",
                "Ensure this field has no more than 4 characters.",
            ],
        ),
    ),
)
def test_doctor_cannot_create_prescription_with_invalid_prescription_code(
    authenticated_doctor, data_fixture, code, expected_error
):
    api_client, _ = authenticated_doctor

    data_fixture["prescription_code"] = code
    url = reverse("prescription-list")
    response = api_client.post(url, data=data_fixture, format="json")

    expected_response = {"prescription_code": expected_error}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_fixture",
    (
        pytest.lazy_fixture("prescription_data"),
        pytest.lazy_fixture("prescription_data_with_visit"),
    ),
)
@pytest.mark.parametrize(
    "amount",
    ((0), (101)),
)
def test_doctor_cannot_create_prescription_with_invalid_dosages_amount(
    authenticated_doctor, data_fixture, amount
):
    api_client, _ = authenticated_doctor

    data_fixture["dosages"][0]["amount"] = amount
    url = reverse("prescription-list")
    response = api_client.post(url, data=data_fixture, format="json")

    expected_error = "Invalid amount. Must be positive and not exceed 100."
    expected_response = {"dosages": [{"amount": [expected_error]}]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_fixture",
    (
        pytest.lazy_fixture("prescription_data"),
        pytest.lazy_fixture("prescription_data_with_visit"),
    ),
)
@pytest.mark.parametrize(
    "value, multiplier",
    (("long", 30),),
)
def test_doctor_cannot_create_prescription_with_invalid_dosages_frequency(
    authenticated_doctor, data_fixture, value, multiplier
):
    api_client, _ = authenticated_doctor

    data_fixture["dosages"][0]["frequency"] = value * multiplier
    url = reverse("prescription-list")
    response = api_client.post(url, data=data_fixture, format="json")

    expected_error = "Ensure this field has no more than 100 characters."
    expected_response = {"dosages": [{"frequency": [expected_error]}]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_create_prescription_with_visit_and_doctor_patient_data_1(
    authenticated_doctor,
    prescription_data_with_visit,
    doctor_instances,
    patient_instances,
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")

    prescription_data_with_visit["doctor"] = doctor_instances[0].pk
    prescription_data_with_visit["patient"] = patient_instances[0].pk

    response = api_client.post(
        url, data=prescription_data_with_visit, format="json"
    )

    expected_error = "Cannot provide patient or doctor when visit is provided."
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_create_prescription_with_visit_and_doctor_patient_data_2(
    authenticated_doctor, prescription_data, visit_instances
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")

    prescription_data["visit"] = visit_instances[0].pk

    response = api_client.post(url, data=prescription_data, format="json")

    expected_error = "Cannot provide patient or doctor when visit is provided."
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_create_prescription_with_no_visit_data(
    authenticated_doctor, prescription_data_with_visit
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")

    prescription_data_with_visit["visit"] = None

    response = api_client.post(
        url, data=prescription_data_with_visit, format="json"
    )

    expected_error = "Either the visit must be provided, or both patient and doctor must be provided."
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
def test_doctor_cannot_create_prescription_with_no_patient_and_doctor_data(
    authenticated_doctor, prescription_data
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")

    prescription_data["doctor"] = None
    prescription_data["patient"] = None

    response = api_client.post(url, data=prescription_data, format="json")

    expected_error = "Either the visit must be provided, or both patient and doctor must be provided."
    expected_response = {"errors": [expected_error]}

    assert (response.status_code, response.data) == (
        status.HTTP_400_BAD_REQUEST,
        expected_response,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data_fixture",
    (
        pytest.lazy_fixture("prescription_data"),
        pytest.lazy_fixture("prescription_data_with_visit"),
    ),
)
def test_doctor_cannot_create_prescription_with_rate_limiting(
    authenticated_doctor, data_fixture
):
    api_client, _ = authenticated_doctor
    url = reverse("prescription-list")

    for _ in range(60):
        response = api_client.post(url, data=data_fixture, format="json")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
