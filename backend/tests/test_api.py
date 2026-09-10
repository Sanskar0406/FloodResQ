import sys
import os
import io
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.seed import seed_database

class TestFloodResQBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        cls.client = TestClient(app)

    def test_01_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "FloodResQ")

    def test_02_stats(self):
        resp = self.client.get("/api/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("citizen_reports", data)
        self.assertIn("people_rescued", data)
        self.assertIn("active_shelters", data)
        self.assertIn("rescue_teams", data)
        self.assertIn("critical_incidents", data)

    def test_03_list_reports(self):
        resp = self.client.get("/api/reports")
        self.assertEqual(resp.status_code, 200)
        reports = resp.json()
        self.assertIsInstance(reports, list)
        self.assertGreater(len(reports), 0)

    def test_04_create_report_with_ai_scoring(self):
        # Test life-threatening report
        resp = self.client.post(
            "/api/reports",
            data={
                "location": "Near Z-Bridge, Pune",
                "description": "Family of 4 trapped on roof, water level chest-deep and rising fast!",
                "need_type": "rescue",
                "lat": 18.518,
                "lng": 73.845
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        rep = data["report"]
        self.assertEqual(rep["urgency"], "critical")
        self.assertIn("trapped", rep["reasoning"].lower())
        # Should have matched a nearest rescue resource
        self.assertIsNotNone(data["matched_resource"])
        self.assertIn("resource", data["matched_resource"])

    def test_05_create_report_with_photo(self):
        dummy_file = io.BytesIO(b"fake image data for testing")
        resp = self.client.post(
            "/api/reports",
            data={
                "location": "Swargate Bus Stand",
                "description": "Ground floor waterlogged, elderly people need dry shelter and food.",
                "need_type": "shelter",
                "lat": 18.502,
                "lng": 73.858
            },
            files={"photo": ("flood_photo.jpg", dummy_file, "image/jpeg")}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["report"]["photo_url"])

    def test_06_emergency_sos(self):
        resp = self.client.post(
            "/api/sos",
            json={
                "location": "Bund Garden Boat Club",
                "lat": 18.535,
                "lng": 73.885,
                "details": "Rapid SOS beacon! Water entered residential complex."
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["urgency"], "critical")
        self.assertIn("report", data)
        self.assertIsNotNone(data["report"]["assigned_resource_id"])

    def test_07_analytics(self):
        resp = self.client.get("/api/analytics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("water_level", data)
        self.assertIn("rainfall", data)
        self.assertIn("risk_forecast", data)
        self.assertIn("incidents", data)
        self.assertEqual(data["water_level"]["danger_threshold"], 6.0)

    def test_08_map_data(self):
        resp = self.client.get("/api/map-data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("points", data)
        self.assertIn("risk_zones", data)
        self.assertGreater(len(data["points"]), 0)

    def test_09_assign_and_resolve_report(self):
        # Create report
        resp = self.client.post(
            "/api/reports/json",
            json={
                "location": "Test Location",
                "description": "Water logging test case",
                "need_type": "food",
                "lat": 18.52,
                "lng": 73.85
            }
        )
        rep_id = resp.json()["report"]["id"]

        # Assign
        resp_assign = self.client.post(
            f"/api/reports/{rep_id}/assign",
            data={"resource_id": "res-04"}
        )
        self.assertEqual(resp_assign.status_code, 200)
        self.assertEqual(resp_assign.json()["report"]["status"], "assigned")

        # Resolve
        resp_resolve = self.client.post(f"/api/reports/{rep_id}/resolve")
        self.assertEqual(resp_resolve.status_code, 200)
        self.assertEqual(resp_resolve.json()["report"]["status"], "resolved")

    def test_10_volunteer_registration(self):
        resp = self.client.post(
            "/api/volunteers",
            json={
                "full_name": "Rohan Deshmukh",
                "dob": "1998-03-22",
                "gender": "Male",
                "email": "rohan.deshmukh@example.com",
                "phone": "9822012345",
                "city": "Pune",
                "state": "Maharashtra",
                "skills": ["Search & Rescue", "Logistics & Supply Distribution"],
                "availability": "Weekends Only",
                "preferred_role": "Field Rescue Support",
                "areas_willing_to_serve": "Shivajinagar & Kothrud",
                "has_transport": True
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("VOL-", data["volunteer_code"])
        self.assertEqual(data["volunteer"]["full_name"], "Rohan Deshmukh")

        # Test listing volunteers
        resp_list = self.client.get("/api/volunteers")
        self.assertEqual(resp_list.status_code, 200)
        volunteers = resp_list.json()
        self.assertIsInstance(volunteers, list)
        self.assertGreater(len(volunteers), 0)

if __name__ == "__main__":
    unittest.main()
