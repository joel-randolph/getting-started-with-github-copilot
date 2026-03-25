"""
FastAPI tests for Mergington High School Activities API.
Uses AAA (Arrange-Act-Assert) pattern for test structure.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


client = TestClient(app)

# Test email addresses
TEST_EMAIL_1 = "test.student.1@mergington.edu"
TEST_EMAIL_2 = "test.student.2@mergington.edu"
TEST_ACTIVITY = "Chess Club"


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Snapshot and restore activities state before/after each test.
    Ensures test isolation without modifying the global state permanently.
    """
    # Snapshot all participants lists before test
    snapshot = {
        activity_name: copy.copy(activity["participants"])
        for activity_name, activity in activities.items()
    }
    
    yield
    
    # Restore all participants lists after test
    for activity_name, participants_snapshot in snapshot.items():
        activities[activity_name]["participants"] = copy.copy(participants_snapshot)


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_200_and_valid_schema(self):
        """
        Arrange: Client ready.
        Act: GET /activities.
        Assert: Status 200, response is dict, each activity has required fields.
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        assert len(activities_data) > 0
        
        # Verify each activity has required schema
        for activity_name, activity in activities_data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self):
        """
        Arrange: Test email ready.
        Act: POST signup with valid activity and email.
        Assert: Status 200, email appears in participants list.
        """
        # Arrange
        email = TEST_EMAIL_1
        activity_name = TEST_ACTIVITY
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        
        # Verify participant added to list
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_signup_duplicate_registration(self):
        """
        Arrange: Email already in participants list.
        Act: POST signup with same email twice.
        Assert: Second request returns 400 with duplicate error.
        """
        # Arrange
        email = TEST_EMAIL_1
        activity_name = TEST_ACTIVITY
        
        # First signup succeeds
        response_1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response_1.status_code == 200
        
        # Act: Try to sign up again
        response_2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response_2.status_code == 400
        assert "already signed up" in response_2.json()["detail"]
    
    def test_signup_activity_not_found(self):
        """
        Arrange: Invalid activity name.
        Act: POST signup to non-existent activity.
        Assert: Status 404 with "Activity not found" message.
        """
        # Arrange
        email = TEST_EMAIL_1
        invalid_activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestDelete:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_delete_success(self):
        """
        Arrange: Email in participants list.
        Act: DELETE signup.
        Assert: Status 200, email removed from participants list.
        """
        # Arrange
        email = TEST_EMAIL_1
        activity_name = TEST_ACTIVITY
        
        # First, sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        
        # Verify participant removed from list
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_delete_activity_not_found(self):
        """
        Arrange: Invalid activity name.
        Act: DELETE signup from non-existent activity.
        Assert: Status 404 with "Activity not found" message.
        """
        # Arrange
        email = TEST_EMAIL_1
        invalid_activity = "Nonexistent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_delete_participant_not_found(self):
        """
        Arrange: Email not in participants list.
        Act: DELETE signup for unregistered email.
        Assert: Status 404 with "not registered" message.
        """
        # Arrange
        email = TEST_EMAIL_1
        activity_name = TEST_ACTIVITY
        
        # Ensure email is NOT in participants
        if email in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].remove(email)
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]
