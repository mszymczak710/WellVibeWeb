import pytest


def test_user_str_representation(user):
    assert str(user) == "Test User (test@example.com)"


@pytest.mark.parametrize(
    "index, expected_str",
    (
        (0, "ul. Ulica 1/1A, 00-000 Miasto, Poland"),
        (1, "ul. Inna Ulica 2, 11-111 Inne Miasto, Poland"),
    ),
)
def test_address_str_representation(address_instances, index, expected_str):
    address = address_instances[index]
    assert str(address) == expected_str
