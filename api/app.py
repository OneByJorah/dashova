import json
import os
from datetime import datetime

from fastapi import Body, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, joinedload, relationship

DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("sqlite"):
    connect_args={"check_same_thread": False}
else:
    connect_args={}
engine=create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base=declarative_base()

class AdminUser(Base):
    __tablename__="admin_users"
    id=Column(Integer, primary_key=True, index=True)
    username=Column(String, unique=True, nullable=False)
    password_hash=Column(String, nullable=False)

class Service(Base):
    __tablename__="services"
    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, nullable=False)
    type=Column(String)

class Staff(Base):
    __tablename__="staff"
    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, nullable=False)
    email=Column(String)
    telegram_id=Column(String)

class AuthEvent(Base):
    __tablename__="auth_events"
    id=Column(Integer, primary_key=True, index=True)
    staff_id=Column(Integer, ForeignKey("staff.id"), nullable=True)
    service_id=Column(Integer, ForeignKey("services.id"), nullable=False)
    event_type=Column(String)
    source_ip=Column(String)
    user_agent=Column(Text)
    metadata_json=Column(Text)
    created_at=Column(DateTime, default=datetime.utcnow)
    staff_rel=relationship("Staff", backref="events")
    service_rel=relationship("Service", backref="events")

Base.metadata.create_all(bind=engine)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

app=FastAPI(title="Dashova API")

_allowed_origins=[
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    return response

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/ingest/service-login")
def ingest_service_login(
    staff_email: str = Body(),
    service_name: str = Body(),
    source_ip: str | None = Body(None),
    user_agent: str | None = Body(None),
    metadata: dict | None = Body(None),
    db: Session = Depends(get_db)
):
    staff=db.query(Staff).filter(Staff.email==staff_email).first()
    if not staff:
        staff=Staff(name=staff_email, email=staff_email)
        db.add(staff); db.commit(); db.refresh(staff)
    service=db.query(Service).filter(Service.name==service_name).first()
    if not service:
        service=Service(name=service_name, type="sso")
        db.add(service); db.commit(); db.refresh(service)
    ev=AuthEvent(staff_id=staff.id, service_id=service.id, event_type="login", source_ip=source_ip, user_agent=user_agent, metadata_json=json.dumps(metadata or {}))
    db.add(ev); db.commit(); db.refresh(ev)
    return {"event_id": ev.id}

@app.get("/admin/events")
def list_events(service: str | None=None, limit: int=50, db: Session=Depends(get_db)):
    q=db.query(AuthEvent).options(joinedload(AuthEvent.service_rel), joinedload(AuthEvent.staff_rel))
    if service:
        q=q.join(Service).filter(Service.name==service)
    rows=q.order_by(AuthEvent.created_at.desc()).limit(limit).all()
    out=[]
    for r in rows:
        out.append({
          "id":r.id,
          "staff_id":r.staff_id,
          "staff_name":r.staff_rel.name if r.staff_rel else None,
          "service":r.service_rel.name if r.service_rel else None,
          "service_id":r.service_id,
          "event_type":r.event_type,
          "source_ip":r.source_ip,
          "user_agent":r.user_agent,
          "metadata":r.metadata_json,
          "created_at":r.created_at.isoformat() if r.created_at else None,
        })
    return out
