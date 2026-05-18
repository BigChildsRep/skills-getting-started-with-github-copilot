import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original_activities


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    with TestClient(app) as client:
        response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert expected_activity in activities
    assert isinstance(activities[expected_activity]["participants"], list)
    assert activities[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    student_email = "alex@mergington.edu"

    with TestClient(app) as client:
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email},
        )

        # Assert
        assert response.status_code == 200
        assert student_email in response.json()["message"]

        follow_up = client.get("/activities")

    assert follow_up.status_code == 200
    activities = follow_up.json()
    assert student_email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_400():
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"

    with TestClient(app) as client:
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": duplicate_email},
        )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_for_missing_activity_returns_404():
    # Arrange
    missing_activity = "Nonexistent Club"
    student_email = "test@mergington.edu"

    with TestClient(app) as client:
        # Act
        response = client.post(
            f"/activities/{missing_activity}/signup",
            params={"email": student_email},
        )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
