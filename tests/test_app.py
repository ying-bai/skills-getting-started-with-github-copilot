from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    initial_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(initial_activities))


# Explanation: This fixture resets the activities to their initial state before each test to ensure test isolation.
@pytest.fixture
def client():
    return TestClient(app)

# Explanation: This test checks that the root endpoint redirects to the static index page.
def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_new_participant(client):
    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 200
    assert "student@example.com" in activities["Soccer Club"]["participants"]
    assert response.json()["message"] == (
        "Signed up student@example.com for Soccer Club"
    )


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    assert response.json()["message"] == (
        "Unregistered michael@mergington.edu from Chess Club"
    )


# Explanation: This test checks that attempting to unregister a participant who is not signed up for the activity returns a 404 error with the appropriate message.
def test_unregister_rejects_unknown_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"

# The following test cases cover the scenarios for unregistering participants from activities.
# They check for successful removal, rejection of unknown participants, and rejection of unknown activities.
def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
