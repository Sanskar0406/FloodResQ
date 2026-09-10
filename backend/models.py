from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from backend.database import Base

# --- SQLAlchemy Models ---

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    need_type = Column(String(50), nullable=False)  # rescue, medical, shelter, food
    photo_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, assigned, resolved
    urgency = Column(String(50), nullable=True, default="medium")  # critical, high, medium, low
    credibility = Column(String(50), nullable=True, default="high")  # high, medium, low
    reasoning = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    assigned_resource_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assigned_resource = relationship("Resource", back_populates="assigned_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "description": self.description,
            "need_type": self.need_type,
            "photo_url": self.photo_url,
            "status": self.status,
            "urgency": self.urgency or "medium",
            "credibility": self.credibility or "medium",
            "reasoning": self.reasoning or "",
            "lat": self.lat,
            "lng": self.lng,
            "assigned_resource_id": self.assigned_resource_id,
            "assigned_resource": self.assigned_resource.to_dict() if self.assigned_resource else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # rescue, medical, shelter, food
    location = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    available = Column(Boolean, default=True, nullable=False)
    contact = Column(String(100), nullable=True)
    capacity = Column(String(100), nullable=True)

    assigned_reports = relationship("Report", back_populates="assigned_resource")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "location": self.location,
            "lat": self.lat,
            "lng": self.lng,
            "available": self.available,
            "contact": self.contact or "Radio Ch-4 / Emergency Line",
            "capacity": self.capacity or "Standard Unit",
        }


# --- Pydantic Schemas ---

class ReportCreate(BaseModel):
    location: str
    description: str
    need_type: str = Field(..., description="rescue, medical, shelter, food")
    photo_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class ReportUpdate(BaseModel):
    status: Optional[str] = None  # pending, assigned, resolved
    urgency: Optional[str] = None
    assigned_resource_id: Optional[str] = None

class SOSRequest(BaseModel):
    location: Optional[str] = "Emergency GPS Location"
    lat: Optional[float] = None
    lng: Optional[float] = None
    details: Optional[str] = "Immediate rescue assistance requested via Emergency SOS button."

class ResourceCreate(BaseModel):
    name: str
    type: str
    location: str
    lat: float
    lng: float
    available: bool = True
    contact: Optional[str] = None
    capacity: Optional[str] = None


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volunteer_code = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    dob = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    alt_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=True)
    skills = Column(Text, nullable=True)
    availability = Column(String(100), nullable=True)
    preferred_role = Column(String(100), nullable=True)
    areas_willing_to_serve = Column(String(255), nullable=True)
    has_transport = Column(Boolean, default=False)
    experience = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "volunteer_code": self.volunteer_code,
            "full_name": self.full_name,
            "dob": self.dob,
            "gender": self.gender,
            "email": self.email,
            "phone": self.phone,
            "alt_phone": self.alt_phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "skills": self.skills.split(", ") if self.skills else [],
            "availability": self.availability,
            "preferred_role": self.preferred_role,
            "areas_willing_to_serve": self.areas_willing_to_serve,
            "has_transport": self.has_transport,
            "experience": self.experience,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_relationship": self.emergency_contact_relationship,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VolunteerCreate(BaseModel):
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    email: str
    phone: str
    alt_phone: Optional[str] = None
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    skills: Optional[List[str]] = []
    availability: Optional[str] = None
    preferred_role: Optional[str] = None
    areas_willing_to_serve: Optional[str] = None
    has_transport: bool = False
    experience: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

