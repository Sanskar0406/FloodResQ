import uuid
from datetime import datetime, timedelta
from backend.database import SessionLocal, Base, engine
from backend.models import Resource, Report

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Resource).count() > 0:
            return

        resources_data = [
            {
                "id": "res-01",
                "name": "Riverside Swift Rescue Team",
                "type": "rescue",
                "location": "Riverside District, Near North Bridge, Pune",
                "lat": 18.5204,
                "lng": 73.8567,
                "available": True,
                "contact": "VHF Ch-16 / +91-20-25501234",
                "capacity": "12 boats / 30 responders"
            },
            {
                "id": "res-02",
                "name": "St. Mary Emergency Medical Unit",
                "type": "medical",
                "location": "Downtown, Central Hospital Campus, Pune",
                "lat": 18.5300,
                "lng": 73.8400,
                "available": True,
                "contact": "Ambulance Dispatch 108",
                "capacity": "4 ICU Ambulances / 8 Paramedics"
            },
            {
                "id": "res-03",
                "name": "Greenfield Community Shelter",
                "type": "shelter",
                "location": "Greenfield, West Side High School Gym, Pune",
                "lat": 18.5000,
                "lng": 73.8100,
                "available": True,
                "contact": "+91-20-24458900",
                "capacity": "350 beds (180 available)"
            },
            {
                "id": "res-04",
                "name": "Harbor Food Distribution Hub",
                "type": "food",
                "location": "Harbor Port, Warehouse 7, Pune",
                "lat": 18.5500,
                "lng": 73.9000,
                "available": True,
                "contact": "+91-20-26871100",
                "capacity": "5,000 meal packs / day"
            },
            {
                "id": "res-05",
                "name": "Eastside Flood Rescue Boat Squad",
                "type": "rescue",
                "location": "Eastside, Canal Lock 3, Pune",
                "lat": 18.5400,
                "lng": 73.8800,
                "available": True,
                "contact": "VHF Ch-08 / +91-20-26684321",
                "capacity": "8 Zodiacs / 24 divers"
            },
            {
                "id": "res-06",
                "name": "Mercy Clinic Mobile Unit",
                "type": "medical",
                "location": "Southgate, Civic Center Parking Lot, Pune",
                "lat": 18.4900,
                "lng": 73.8500,
                "available": True,
                "contact": "Mobile Unit +91-20-24263000",
                "capacity": "Field trauma kit & triage station"
            },
            {
                "id": "res-07",
                "name": "Hadapsar Rescue Squad",
                "type": "rescue",
                "location": "Hadapsar Fire Station, Pune",
                "lat": 18.5080,
                "lng": 73.9290,
                "available": True,
                "contact": "+91-20-26992211",
                "capacity": "Heavy rescue truck & 4 motorized rafts"
            },
            {
                "id": "res-08",
                "name": "Kothrud Medical Camp",
                "type": "medical",
                "location": "Kothrud Sports Complex, Pune",
                "lat": 18.5070,
                "lng": 73.8080,
                "available": True,
                "contact": "+91-20-25447788",
                "capacity": "Doctor team & emergency pharmaceuticals"
            },
            {
                "id": "res-09",
                "name": "Baner Shelter Center",
                "type": "shelter",
                "location": "Baner Cultural Center, Pune",
                "lat": 18.5600,
                "lng": 73.7700,
                "available": True,
                "contact": "+91-20-27293344",
                "capacity": "470 beds (260 available)"
            },
            {
                "id": "res-10",
                "name": "Kharadi Food Relief Station",
                "type": "food",
                "location": "Kharadi Community Ground, Pune",
                "lat": 18.5600,
                "lng": 73.9400,
                "available": True,
                "contact": "+91-20-27038899",
                "capacity": "3,500 ration kits / day"
            }
        ]

        for item in resources_data:
            db.add(Resource(**item))

        reports_data = [
            {
                "id": "rep-01",
                "location": "Sangam Bridge, Mula-Mutha Confluence, Pune",
                "description": "Elderly couple and 2 children trapped on 1st floor balcony. Water level rapidly rising, current too strong to swim.",
                "need_type": "rescue",
                "status": "pending",
                "urgency": "critical",
                "credibility": "high",
                "reasoning": "Life-threatening situation: Trapped family with children and fast-rising flood waters.",
                "lat": 18.5300,
                "lng": 73.8600,
                "assigned_resource_id": None,
                "created_at": datetime.utcnow() - timedelta(minutes=15)
            },
            {
                "id": "rep-02",
                "location": "Shivajinagar, near Railway Station Subway",
                "description": "Car submerged up to windshield under railway bridge. Driver stuck inside, water entering vehicle cabin.",
                "need_type": "rescue",
                "status": "pending",
                "urgency": "critical",
                "credibility": "high",
                "reasoning": "Critical vehicle submergence with occupant trapped inside.",
                "lat": 18.5350,
                "lng": 73.8450,
                "assigned_resource_id": None,
                "created_at": datetime.utcnow() - timedelta(minutes=24)
            },
            {
                "id": "rep-03",
                "location": "Deccan Gymkhana, Riverside Road",
                "description": "Diabetic patient with high fever cut off by 3-foot waterlogging. Needs insulin and medical evacuation.",
                "need_type": "medical",
                "status": "assigned",
                "urgency": "high",
                "credibility": "high",
                "reasoning": "High urgency: Medical condition requiring prompt access to insulin and clinical care.",
                "lat": 18.5150,
                "lng": 73.8420,
                "assigned_resource_id": "res-02",
                "created_at": datetime.utcnow() - timedelta(minutes=48)
            },
            {
                "id": "rep-04",
                "location": "Yerawada, Shanti Nagar Slum Area",
                "description": "Over 40 families displaced as river overflowed embankment. Looking for dry shelter, blankets, and safe drinking water.",
                "need_type": "shelter",
                "status": "pending",
                "urgency": "high",
                "credibility": "high",
                "reasoning": "High priority: Large displacement of families requiring emergency temporary shelter.",
                "lat": 18.5520,
                "lng": 73.8820,
                "assigned_resource_id": None,
                "created_at": datetime.utcnow() - timedelta(hours=1, minutes=10)
            },
            {
                "id": "rep-05",
                "location": "Kalyani Nagar, Jogger's Park Lane",
                "description": "Drinking water pipelines contaminated. 150 residents require clean drinking water and food packets.",
                "need_type": "food",
                "status": "pending",
                "urgency": "medium",
                "credibility": "high",
                "reasoning": "Medium urgency: Essential relief supply needed; no immediate danger of drowning.",
                "lat": 18.5460,
                "lng": 73.9030,
                "assigned_resource_id": None,
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "id": "rep-06",
                "location": "Aundh, Rajiv Gandhi Bridge approach",
                "description": "Water receded to sidewalk level. Road clear for emergency vehicles, minor debris remaining.",
                "need_type": "rescue",
                "status": "resolved",
                "urgency": "low",
                "credibility": "high",
                "reasoning": "Low urgency: Receding waters, safe for traffic.",
                "lat": 18.5620,
                "lng": 73.8050,
                "assigned_resource_id": None,
                "created_at": datetime.utcnow() - timedelta(hours=4)
            }
        ]

        for item in reports_data:
            db.add(Report(**item))

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")
