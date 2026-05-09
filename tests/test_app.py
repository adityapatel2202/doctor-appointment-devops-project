import requests

BASE_URL = "http://localhost:5000"


def test_home_page():
    response = requests.get(BASE_URL)

    assert response.status_code == 200


def test_patient_login_page():
    response = requests.get(f"{BASE_URL}/patient/login")

    assert response.status_code == 200


def test_doctor_login_page():
    response = requests.get(f"{BASE_URL}/doctor/login")

    assert response.status_code == 200


def test_patient_register_page():
    response = requests.get(f"{BASE_URL}/patient/register")

    assert response.status_code == 200


def test_doctor_register_page():
    response = requests.get(f"{BASE_URL}/doctor/register")

    assert response.status_code == 200