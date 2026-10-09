"""Normalized relational schema, shared by SQLite and PostgreSQL."""
import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, Column, Integer, String, Text, Float, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DATA = ROOT / 'backend' / 'data'
DATA.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL') or 'sqlite:///' + str(DATA / 'internflow.db').replace('\\', '/')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_constraints(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=5000')
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Branch(Base):
    __tablename__ = 'branches'
    name = Column(String(100), primary_key=True)

class InternshipBranch(Base):
    __tablename__ = 'internship_branches'
    internship_id = Column(Integer, ForeignKey('internships.id', ondelete='CASCADE'), primary_key=True)
    branch_name = Column(String(100), ForeignKey('branches.name'), primary_key=True)

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    college = Column(String(200), nullable=False)
    branch = Column(String(100), ForeignKey('branches.name'), nullable=False)
    year = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=False)
    graduation_year = Column(Integer, nullable=False)
    bio = Column(Text, default='')
    experience_months = Column(Integer, default=0, nullable=False)
    __table_args__ = (CheckConstraint('cgpa >= 0 AND cgpa <= 10'), CheckConstraint('year >= 1 AND year <= 5'), CheckConstraint('experience_months >= 0'))

class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)

class StudentSkill(Base):
    __tablename__ = 'student_skills'
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, default='')
    domain = Column(String(80), nullable=False)

class Preference(Base):
    __tablename__ = 'preferences'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    value = Column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint('student_id', 'kind', 'value'), CheckConstraint("kind IN ('domain','location')"))

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    color = Column(String(20), default='#405a45')

class Internship(Base):
    __tablename__ = 'internships'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    role = Column(String(180), nullable=False)
    domain = Column(String(80), nullable=False)
    location = Column(String(120), nullable=False)
    work_mode = Column(String(30), nullable=False)
    stipend = Column(Integer, default=0, nullable=False)
    duration_months = Column(Integer, nullable=False)
    min_cgpa = Column(Float, nullable=False)
    eligible_year = Column(Integer, nullable=False)
    eligible_branches = relationship('Branch', secondary='internship_branches')
    @property
    def eligible_branch(self):
        return ', '.join(b.name for b in self.eligible_branches) or 'Any'
    experience_months = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=False)
    application_url = Column(Text, default='')
    source = Column(String(100), default='Manual import')
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    __table_args__ = (CheckConstraint('min_cgpa >= 0 AND min_cgpa <= 10'), CheckConstraint('eligible_year >= 1 AND eligible_year <= 5'), CheckConstraint('stipend >= 0'), CheckConstraint('duration_months >= 1 AND duration_months <= 24'), CheckConstraint('experience_months >= 0'), CheckConstraint("work_mode IN ('On-site','Remote','Hybrid')"), UniqueConstraint('company_id', 'role', 'location'))

class InternshipSkill(Base):
    __tablename__ = 'internship_skills'
    internship_id = Column(Integer, ForeignKey('internships.id', ondelete='CASCADE'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)

class TimelineEvent(Base):
    __tablename__ = 'timeline_events'
    id = Column(Integer, primary_key=True)
    internship_id = Column(Integer, ForeignKey('internships.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    starts_at = Column(DateTime, nullable=False, index=True)
    __table_args__ = (UniqueConstraint('internship_id', 'kind'), CheckConstraint("kind IN ('deadline','oa','ppt')"))

class Bookmark(Base):
    __tablename__ = 'bookmarks'
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True)
    internship_id = Column(Integer, ForeignKey('internships.id', ondelete='CASCADE'), primary_key=True)

STATUSES = ('Draft', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    internship_id = Column(Integer, ForeignKey('internships.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(30), default='Draft', nullable=False)
    cover_letter = Column(Text, default='')
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint('student_id', 'internship_id'), CheckConstraint("status IN ('Draft','Applied','Assessment','Interview','Offer','Rejected','Withdrawn')"))

class ApplicationHistory(Base):
    __tablename__ = 'application_history'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    changed_at = Column(DateTime, default=utcnow, nullable=False)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(String(36), primary_key=True)
    kind = Column(String(40), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

class Ingestion(Base):
    __tablename__ = 'ingestions'
    id = Column(Integer, primary_key=True)
    source_hash = Column(String(64), unique=True, nullable=False)
    internship_id = Column(Integer, ForeignKey('internships.id'), nullable=False)
    document_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

def get_db():
    with SessionLocal() as session:
        yield session
