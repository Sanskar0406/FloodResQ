import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db, Base, engine
from backend.models import Report, Resource, ReportCreate, ReportUpdate, SOSRequest, ResourceCreate, Volunteer, VolunteerCreate
from backend.ai_service import score_report
from backend.geo_service import find_nearest_resource
from backend.seed import seed_database

# Base Directories
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB & Seeds
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

app = FastAPI(
    title="FloodResQ API",
    description="Backend API for AI-assisted flood monitoring and emergency response",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- API Endpoints -----------------

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": "FloodResQ",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": bool(os.environ.get("GEMINI_API_KEY"))
    }

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_reports = db.query(Report).count()
    critical_count = db.query(Report).filter(Report.urgency == "critical", Report.status != "resolved").count()
    high_count = db.query(Report).filter(Report.urgency == "high", Report.status != "resolved").count()
    moderate_count = db.query(Report).filter(Report.urgency == "medium", Report.status != "resolved").count()
    resolved_count = db.query(Report).filter(Report.status == "resolved").count()

    active_rescue_teams = db.query(Resource).filter(Resource.type == "rescue", Resource.available == True).count()
    shelters_count = db.query(Resource).filter(Resource.type == "shelter").count()

    return {
        "citizen_reports": 1240 + total_reports,
        "people_rescued": 436 + (resolved_count * 5),
        "active_shelters": 70 + shelters_count,
        "rescue_teams": 15 + active_rescue_teams,
        "cities_covered": 12,
        "critical_incidents": critical_count,
        "high_priority": high_count,
        "moderate_priority": moderate_count,
        "available_rescue_teams": active_rescue_teams,
        "shelter_capacity": 820,
        "total_active_reports": db.query(Report).filter(Report.status != "resolved").count()
    }

@app.get("/api/reports")
def list_reports(
    status: Optional[str] = None,
    need_type: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    if status and status != "all":
        query = query.filter(Report.status == status)
    if need_type and need_type != "all":
        query = query.filter(Report.need_type == need_type)
    if urgency and urgency != "all":
        query = query.filter(Report.urgency == urgency)

    reports = query.order_by(desc(Report.created_at)).limit(limit).all()

    # Custom sort: critical > high > medium > low; unassigned before assigned
    urgency_weights = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    def sort_key(r):
        is_assigned = 1 if (r.status == "assigned" or r.assigned_resource_id) else 0
        urg = urgency_weights.get(r.urgency, 9)
        return (is_assigned, urg)

    sorted_reports = sorted(reports, key=sort_key)
    return [r.to_dict() for r in sorted_reports]

def parse_optional_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        val_str = str(val).strip().lower()
        if val_str in ("null", "undefined", "none", "", "nan"):
            return None
        return float(val)
    except (ValueError, TypeError):
        return None

@app.post("/api/reports")
async def create_report(
    location: str = Form(...),
    description: str = Form(...),
    need_type: str = Form(...),
    lat: Optional[str] = Form(None),
    lng: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    parsed_lat = parse_optional_float(lat)
    parsed_lng = parse_optional_float(lng)

    photo_url = None
    photo_bytes = None
    photo_mime = "image/jpeg"

    if photo and photo.filename:
        filename = f"{uuid.uuid4().hex}_{os.path.basename(photo.filename)}"
        filepath = os.path.join(UPLOADS_DIR, filename)
        photo_bytes = await photo.read()
        photo_mime = photo.content_type or "image/jpeg"
        with open(filepath, "wb") as f:
            f.write(photo_bytes)
        photo_url = f"/uploads/{filename}"

    # Perform AI triage scoring
    scoring = await score_report(description, need_type, photo_bytes, photo_mime)

    report = Report(
        id=str(uuid.uuid4()),
        location=location,
        description=description,
        need_type=need_type,
        photo_url=photo_url,
        status="pending",
        urgency=scoring["urgency"],
        credibility=scoring["credibility"],
        reasoning=scoring["reasoning"],
        lat=parsed_lat,
        lng=parsed_lng,
        created_at=datetime.now(timezone.utc)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Match nearest resource
    all_resources = db.query(Resource).all()
    matched = find_nearest_resource(parsed_lat, parsed_lng, need_type, all_resources)

    return {
        "success": True,
        "report": report.to_dict(),
        "matched_resource": matched,
        "message": "Report received and AI priority scored successfully."
    }

@app.post("/api/reports/json")
async def create_report_json(payload: ReportCreate, db: Session = Depends(get_db)):
    """JSON alternative for headless/script submissions."""
    scoring = await score_report(payload.description, payload.need_type)
    report = Report(
        id=str(uuid.uuid4()),
        location=payload.location,
        description=payload.description,
        need_type=payload.need_type,
        photo_url=payload.photo_url,
        status="pending",
        urgency=scoring["urgency"],
        credibility=scoring["credibility"],
        reasoning=scoring["reasoning"],
        lat=payload.lat,
        lng=payload.lng,
        created_at=datetime.now(timezone.utc)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    all_resources = db.query(Resource).all()
    matched = find_nearest_resource(payload.lat, payload.lng, payload.need_type, all_resources)

    return {
        "success": True,
        "report": report.to_dict(),
        "matched_resource": matched
    }

@app.get("/api/reports/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    clean_id = report_id.strip().lstrip("#")
    report = db.query(Report).filter(
        (Report.id == clean_id) | (Report.id.like(f"{clean_id}%"))
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    result = report.to_dict()
    all_resources = db.query(Resource).all()
    nearest = find_nearest_resource(report.lat, report.lng, report.need_type, all_resources)
    result["recommended_resource"] = nearest
    return result

@app.patch("/api/reports/{report_id}")
def update_report(report_id: str, payload: ReportUpdate, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if payload.status is not None:
        report.status = payload.status
    if payload.urgency is not None:
        report.urgency = payload.urgency
    if payload.assigned_resource_id is not None:
        report.assigned_resource_id = payload.assigned_resource_id

    db.commit()
    db.refresh(report)
    return report.to_dict()

@app.post("/api/reports/{report_id}/assign")
def assign_resource_to_report(report_id: str, resource_id: str = Form(...), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    report.assigned_resource_id = resource.id
    report.status = "assigned"
    db.commit()
    db.refresh(report)

    return {
        "success": True,
        "report": report.to_dict(),
        "assigned_resource": resource.to_dict()
    }

@app.post("/api/reports/{report_id}/resolve")
def resolve_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "resolved"
    db.commit()
    db.refresh(report)
    return {"success": True, "message": "Incident marked as resolved.", "report": report.to_dict()}

@app.get("/api/resources")
def list_resources(type: Optional[str] = None, available_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Resource)
    if type and type != "all":
        query = query.filter(Resource.type == type)
    if available_only:
        query = query.filter(Resource.available == True)

    resources = query.all()
    res_list = []
    for r in resources:
        item = r.to_dict()
        item["active_assignments"] = len([rep for rep in r.assigned_reports if rep.status != "resolved"])
        res_list.append(item)
    return res_list

@app.post("/api/resources")
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db)):
    res = Resource(
        id=f"res-{uuid.uuid4().hex[:6]}",
        name=payload.name,
        type=payload.type,
        location=payload.location,
        lat=payload.lat,
        lng=payload.lng,
        available=payload.available,
        contact=payload.contact,
        capacity=payload.capacity
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res.to_dict()

@app.post("/api/volunteers")
def register_volunteer(payload: VolunteerCreate, db: Session = Depends(get_db)):
    code_num = str(uuid.uuid4().int)[:5]
    code = f"VOL-{code_num}"
    skills_str = ", ".join(payload.skills) if payload.skills else ""

    vol = Volunteer(
        id=str(uuid.uuid4()),
        volunteer_code=code,
        full_name=payload.full_name,
        dob=payload.dob,
        gender=payload.gender,
        email=payload.email,
        phone=payload.phone,
        alt_phone=payload.alt_phone,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        skills=skills_str,
        availability=payload.availability,
        preferred_role=payload.preferred_role,
        areas_willing_to_serve=payload.areas_willing_to_serve,
        has_transport=payload.has_transport,
        experience=payload.experience,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_relationship=payload.emergency_contact_relationship,
        emergency_contact_phone=payload.emergency_contact_phone,
        created_at=datetime.now(timezone.utc)
    )
    db.add(vol)
    db.commit()
    db.refresh(vol)
    return {
        "success": True,
        "volunteer": vol.to_dict(),
        "volunteer_code": code,
        "message": "Volunteer registered successfully. Welcome to FloodResQ Disaster Response Network!"
    }

@app.get("/api/volunteers")
def list_volunteers(db: Session = Depends(get_db)):
    volunteers = db.query(Volunteer).order_by(desc(Volunteer.created_at)).all()
    return [v.to_dict() for v in volunteers]

@app.post("/api/sos")
async def trigger_emergency_sos(payload: SOSRequest, db: Session = Depends(get_db)):
    """Immediate high-priority emergency rescue trigger."""
    location_str = payload.location or "GPS Direct Rescue Beacon"
    description_str = payload.details or "Immediate life-saving evacuation requested via Emergency SOS button."

    report = Report(
        id=str(uuid.uuid4()),
        location=location_str,
        description=description_str,
        need_type="rescue",
        status="pending",
        urgency="critical",
        credibility="high",
        reasoning="CRITICAL: Emergency SOS button triggered. Automatic life-safety dispatch alert initiated.",
        lat=payload.lat,
        lng=payload.lng,
        created_at=datetime.now(timezone.utc)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    all_resources = db.query(Resource).all()
    matched = find_nearest_resource(payload.lat, payload.lng, "rescue", all_resources)

    # Automatically reserve/assign the nearest available rescue unit if found
    if matched and matched.get("resource"):
        res_id = matched["resource"]["id"]
        report.assigned_resource_id = res_id
        report.status = "assigned"
        db.commit()
        db.refresh(report)

    return {
        "success": True,
        "sos_id": report.id,
        "urgency": "critical",
        "message": "Emergency SOS received! Rescue teams alerted with highest priority.",
        "report": report.to_dict(),
        "dispatched_unit": matched
    }

@app.get("/api/analytics")
def get_analytics():
    return {
        "water_level": {
            "title": "River Water Level (m)",
            "river": "Mula-Mutha River, Pune Basin",
            "current_value": 4.8,
            "unit": "m",
            "danger_threshold": 6.0,
            "warning_threshold": 4.5,
            "trend": "Rising",
            "trend_direction": "up",
            "alert": "Water level rising in Mula-Mutha River. High flood risk at low-lying riverbank areas.",
            "times": ["12 AM", "4 AM", "8 AM", "12 PM", "4 PM", "8 PM"],
            "values": [3.1, 3.4, 3.8, 4.1, 4.5, 4.8],
            "danger_values": [6.0, 6.0, 6.0, 6.0, 6.0, 6.0]
        },
        "rainfall": {
            "title": "Precipitation Accumulation (mm)",
            "river": "Pune District Catchment",
            "current_value": 92.4,
            "unit": "mm",
            "danger_threshold": 120.0,
            "warning_threshold": 80.0,
            "trend": "Heavy downpour continuing",
            "trend_direction": "up",
            "alert": "Red Warning: 92.4 mm rainfall recorded in past 12 hrs. Waterlogging expected in urban corridors.",
            "times": ["12 AM", "4 AM", "8 AM", "12 PM", "4 PM", "8 PM"],
            "values": [12.0, 24.5, 45.0, 68.2, 81.0, 92.4]
        },
        "risk_forecast": {
            "title": "AI Flood Risk Probability Forecast (%)",
            "river": "AI Hydrological Prediction Model",
            "current_value": 84,
            "unit": "%",
            "danger_threshold": 75,
            "warning_threshold": 50,
            "trend": "High Probability (Next 6 hrs)",
            "trend_direction": "up",
            "alert": "Predictive model warns of 84% flood probability around Sangamwadi & Deccan Gymkhana by midnight.",
            "times": ["Now", "+2 hrs", "+4 hrs", "+6 hrs", "+8 hrs", "+12 hrs"],
            "values": [65, 74, 84, 88, 79, 62]
        },
        "incidents": {
            "title": "Incident Reports Frequency",
            "river": "Citizen Emergency Reports Inflow",
            "current_value": 38,
            "unit": "calls/hr",
            "danger_threshold": 30,
            "warning_threshold": 20,
            "trend": "+22% past 2 hrs",
            "trend_direction": "up",
            "alert": "High influx of citizen distress calls regarding water trapped vehicles and basement flooding.",
            "times": ["12 AM", "4 AM", "8 AM", "12 PM", "4 PM", "8 PM"],
            "values": [4, 7, 14, 22, 31, 38]
        }
    }

@app.get("/api/map-data")
def get_map_data(db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.status != "resolved").all()
    resources = db.query(Resource).all()

    points = []

    # Map reports
    for r in reports:
        if r.lat is not None and r.lng is not None:
            points.append({
                "type": "incident",
                "id": r.id,
                "title": r.location,
                "description": r.description,
                "need_type": r.need_type,
                "urgency": r.urgency,
                "status": r.status,
                "lat": r.lat,
                "lng": r.lng,
                "assigned_resource_id": r.assigned_resource_id
            })

    # Map resources
    for res in resources:
        if res.lat is not None and res.lng is not None:
            points.append({
                "type": "resource",
                "id": res.id,
                "title": res.name,
                "resource_type": res.type,
                "location": res.location,
                "available": res.available,
                "contact": res.contact,
                "capacity": res.capacity,
                "lat": res.lat,
                "lng": res.lng
            })

    # Flood risk zones
    risk_zones = [
        {"name": "Mula-Mutha Confluence Lowland", "risk": "high", "lat": 18.528, "lng": 73.864, "radius_m": 1200},
        {"name": "Deccan Riverside Causeway", "risk": "high", "lat": 18.514, "lng": 73.840, "radius_m": 800},
        {"name": "Yerawada Embankment Corridor", "risk": "moderate", "lat": 18.550, "lng": 73.880, "radius_m": 1000},
        {"name": "Aundh Low-Lying Canal Area", "risk": "low", "lat": 18.560, "lng": 73.805, "radius_m": 700}
    ]

    return {
        "points": points,
        "risk_zones": risk_zones,
        "center": {"lat": 18.5204, "lng": 73.8567, "zoom": 13}
    }

# ----------------- Static File Serving -----------------

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Mount frontend directory for index.html, report.html, styles, scripts
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
