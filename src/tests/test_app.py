"""
End-to-end tests for the Mergington High School API
Tests cover activities endpoints and signup functionality
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoints"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that response is a dictionary
        assert isinstance(data, dict)
        
        # Verify expected activities are present
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Debate Club",
            "Science Olympiad",
            "Drama Club",
            "Art Studio"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup adds the participant to the activity"""
        email = "testuser@mergington.edu"
        
        # Sign up
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities["Programming Class"]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_when_activity_at_max_capacity_fails(self, client):
        """Test that signing up for a full activity fails"""
        # Chess Club has max_participants=12, and we'll fill it
        # Get current participants
        activities = client.get("/activities").json()
        chess_club = activities["Chess Club"]
        current_count = len(chess_club["participants"])
        max_capacity = chess_club["max_participants"]
        
        # If there's room, fill it up
        if current_count < max_capacity:
            for i in range(max_capacity - current_count):
                email = f"student{i}@mergington.edu"
                client.post(
                    "/activities/Chess Club/signup",
                    params={"email": email}
                )
        
        # Now try to sign up when full (should fail)
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overfull@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "at maximum capacity" in data["detail"].lower()

    def test_signup_duplicate_prevents_double_signup(self, client):
        """Test that a student cannot sign up for the same activity twice"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
