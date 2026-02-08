"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_duplicate_registration(self):
        """Test that duplicate signup fails"""
        email = "duplicate@mergington.edu"
        # First signup
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        # Try to signup again
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_activity_full(self):
        """Test signup when activity is at max capacity"""
        # Create an activity with 1 max participant
        from app import activities
        activities["Small Club"] = {
            "description": "Small activity",
            "schedule": "Monday, 3:00 PM",
            "max_participants": 1,
            "participants": ["existing@mergington.edu"]
        }
        
        response = client.post(
            "/activities/Small%20Club/signup?email=new@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        # First signup
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        # Then unregister
        response = client.delete(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_not_registered(self):
        """Test unregistration for participant not in activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_activity_not_found(self):
        """Test unregistration from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregistration actually removes the participant"""
        email = "verify@mergington.edu"
        # Signup
        client.post(f"/activities/Art%20Studio/signup?email={email}")
        # Verify participant is in list
        response = client.get("/activities")
        assert email in response.json()["Art Studio"]["participants"]
        # Unregister
        client.delete(f"/activities/Art%20Studio/unregister?email={email}")
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307


class TestIntegration:
    """Integration tests for full workflows"""

    def test_signup_and_unregister_workflow(self):
        """Test complete workflow of signup and unregister"""
        email = "workflow@mergington.edu"
        activity = "Robotics%20Club"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Robotics Club"]["participants"])
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        assert len(response.json()["Robotics Club"]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        assert len(response.json()["Robotics Club"]["participants"]) == initial_count
