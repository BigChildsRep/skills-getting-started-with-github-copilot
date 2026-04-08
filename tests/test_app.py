"""Comprehensive tests for the Mergington High School Activities API using AAA pattern"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html"""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successfully fetching all activities"""
        # Arrange
        expected_status = 200
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", "Tennis Team", "Basketball Team", "Debate Club", "Art Studio"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert isinstance(data, dict)
        for activity in expected_activities:
            assert activity in data
    
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that activities contain all required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"
                if field == "participants":
                    assert isinstance(activity_data[field], list)
    
    def test_participants_are_valid_emails(self, client, reset_activities):
        """Test that all participants have email format"""
        # Arrange
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_data in data.values():
            for participant in activity_data["participants"]:
                assert "@" in participant, f"Invalid email format: {participant}"
                assert "." in participant.split("@")[1], f"Invalid email domain: {participant}"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup to an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        expected_status = 200
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "coder@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """Test that signup increments the participant count"""
        # Arrange
        activity_name = "Tennis Team"
        email = "tennis@mergington.edu"
        
        # Get initial count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        
        # Assert
        assert final_count == initial_count + 1
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test that cannot signup if already registered"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        expected_status = 400
        expected_error = "already registered"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error in response.json()["detail"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup with non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        expected_status = 404
        expected_error = "not found"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error in response.json()["detail"]
    
    def test_signup_activity_at_capacity(self, client, reset_activities):
        """Test signup fails when activity is at maximum capacity"""
        # Arrange
        activity_name = "Tennis Team"  # max_participants = 16, currently has 1
        expected_status = 400
        expected_error = "maximum capacity"
        
        # Fill the activity to capacity
        for i in range(15):
            email = f"player{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act - try to signup when full
        response = client.post(
            f"/activities/{activity_name}/signup?email=overflow@mergington.edu"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error in response.json()["detail"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        expected_status = 200
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "Removed" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_remove_participant_actually_removes(self, client, reset_activities):
        """Test that removal actually removes the participant from the activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # Already registered
        
        # Verify participant is registered
        response_before = client.get("/activities")
        assert email in response_before.json()[activity_name]["participants"]
        
        # Act
        client.delete(f"/activities/{activity_name}/participants/{email}")
        response_after = client.get("/activities")
        
        # Assert
        assert email not in response_after.json()[activity_name]["participants"]
    
    def test_remove_participant_decrements_count(self, client, reset_activities):
        """Test that removal decrements the participant count"""
        # Arrange
        activity_name = "Art Studio"
        email = "isabella@mergington.edu"  # Already registered
        
        # Get initial count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Act
        client.delete(f"/activities/{activity_name}/participants/{email}")
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        
        # Assert
        assert final_count == initial_count - 1
    
    def test_remove_participant_not_found(self, client, reset_activities):
        """Test removing a participant that doesn't exist"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"
        expected_status = 404
        expected_error = "not found"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error in response.json()["detail"]
    
    def test_remove_from_nonexistent_activity(self, client, reset_activities):
        """Test removing a participant from non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        expected_status = 404
        expected_error = "not found"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error in response.json()["detail"]
    
    def test_remove_creates_availability(self, client, reset_activities):
        """Test that removing a participant frees up a spot for new signups"""
        # Arrange
        activity_name = "Tennis Team"
        removed_email = "alex@mergington.edu"
        new_email = "newplayer@mergington.edu"
        
        # Fill to capacity
        for i in range(15):
            email = f"player{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify at capacity
        response_full = client.post(
            f"/activities/{activity_name}/signup?email=willnotfit@mergington.edu"
        )
        assert response_full.status_code == 400
        
        # Act - remove one participant
        client.delete(f"/activities/{activity_name}/participants/{removed_email}")
        
        # Act - try signing up again
        response_new = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response_new.status_code == 200
        assert new_email in client.get("/activities").json()[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests for multi-step scenarios"""
    
    def test_signup_then_remove_then_signup_again(self, client, reset_activities):
        """Test the complete flow: signup, remove, and signup again"""
        # Arrange
        activity_name = "Art Studio"
        email = "artist@mergington.edu"
        
        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - First signup succeeded
        assert response1.status_code == 200
        
        # Verify participant is in activity
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Act - Remove
        response2 = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert - Removal succeeded
        assert response2.status_code == 200
        
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
        
        # Act - Signup again
        response3 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - Second signup succeeded
        assert response3.status_code == 200
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
    
    def test_multiple_signups_multiple_activities(self, client, reset_activities):
        """Test signing up for multiple different activities"""
        # Arrange
        student_email = "polymath@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act - Sign up for each activity
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={student_email}"
            )
            assert response.status_code == 200
        
        # Assert - Verify signed up for all activities
        response = client.get("/activities")
        activities_data = response.json()
        for activity in activities_to_join:
            assert student_email in activities_data[activity]["participants"]
    
    def test_signup_and_remove_preserves_other_participants(self, client, reset_activities):
        """Test that signup/removal of one participant doesn't affect others"""
        # Arrange
        activity_name = "Debate Club"
        new_email = "debater@mergington.edu"
        sarah = "sarah@mergington.edu"  # Already registered
        
        # Get initial state
        response_initial = client.get("/activities")
        initial_participants = set(response_initial.json()[activity_name]["participants"])
        
        # Act - Add new participant
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert - Original participants still there
        response = client.get("/activities")
        final_participants = response.json()[activity_name]["participants"]
        assert sarah in final_participants
        assert new_email in final_participants
        
        # Act - Remove new participant
        client.delete(f"/activities/{activity_name}/participants/{new_email}")
        
        # Assert - Back to original state
        response_final = client.get("/activities")
        final_participants_after_remove = response_final.json()[activity_name]["participants"]
        assert sarah in final_participants_after_remove
        # The set should match original participants
        assert set(final_participants_after_remove) == initial_participants
