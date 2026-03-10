"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import Session, declarative_base, relationship
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

Base = declarative_base()


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    max_participants = Column(Integer, nullable=False)
    enrollments = relationship("Enrollment", back_populates="activity", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("activity_id", "user_id", name="uq_activity_user"),)

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity = relationship("Activity", back_populates="enrollments")
    user = relationship("User", back_populates="enrollments")


SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

db_dir = current_dir / "data"
db_dir.mkdir(parents=True, exist_ok=True)
db_path = db_dir / "school.sqlite"
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def bootstrap_database() -> None:
    """Create schema and seed baseline records once for local development."""
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        existing = session.scalar(select(Activity.id).limit(1))
        if existing:
            return

        users_by_email = {}
        for activity_name, details in SEED_ACTIVITIES.items():
            activity = Activity(
                name=activity_name,
                description=details["description"],
                schedule=details["schedule"],
                max_participants=details["max_participants"],
            )
            session.add(activity)
            session.flush()

            for email in details["participants"]:
                user = users_by_email.get(email)
                if user is None:
                    user = session.scalar(select(User).where(User.email == email))
                if user is None:
                    user = User(email=email)
                    session.add(user)
                    session.flush()
                users_by_email[email] = user
                session.add(Enrollment(activity_id=activity.id, user_id=user.id))

        session.commit()


bootstrap_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        all_activities = session.scalars(select(Activity).order_by(Activity.name.asc())).all()
        activity_payload = {}
        for activity in all_activities:
            participants = [
                enrollment.user.email for enrollment in sorted(
                    activity.enrollments,
                    key=lambda enrollment: enrollment.user.email,
                )
            ]
            activity_payload[activity.name] = {
                "description": activity.description,
                "schedule": activity.schedule,
                "max_participants": activity.max_participants,
                "participants": participants,
            }
        return activity_payload


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with Session(engine) as session:
        activity = session.scalar(select(Activity).where(Activity.name == activity_name))
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email)
            session.add(user)
            session.flush()

        existing_enrollment = session.scalar(
            select(Enrollment).where(
                Enrollment.activity_id == activity.id,
                Enrollment.user_id == user.id,
            )
        )
        if existing_enrollment is not None:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

        current_enrollment_count = session.scalar(
            select(func.count(Enrollment.id)).where(Enrollment.activity_id == activity.id)
        )

        if current_enrollment_count >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        session.add(Enrollment(activity_id=activity.id, user_id=user.id))
        session.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with Session(engine) as session:
        activity = session.scalar(select(Activity).where(Activity.name == activity_name))
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        enrollment = session.scalar(
            select(Enrollment).where(
                Enrollment.activity_id == activity.id,
                Enrollment.user_id == user.id,
            )
        )
        if enrollment is None:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        session.delete(enrollment)
        session.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
