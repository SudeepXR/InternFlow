from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse

class ProjectInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default='', max_length=2000)
    domain: str = Field(default='Software Development', max_length=80)

class ProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    college: str = Field(min_length=1, max_length=200)
    branch: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1, le=5)
    cgpa: float = Field(ge=0, le=10)
    graduation_year: int = Field(ge=2020, le=2040)
    bio: str = Field(default='', max_length=3000)
    experience_months: int = Field(default=0, ge=0, le=240)
    skills: list[str] = Field(default_factory=list, max_length=100)
    domains: list[str] = Field(default_factory=list, max_length=20)
    locations: list[str] = Field(default_factory=list, max_length=20)
    projects: list[ProjectInput] = Field(default_factory=list, max_length=30)
    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        if '@' not in value or '.' not in value.rsplit('@',1)[-1]:
            raise ValueError('Enter a valid email address')
        return value
    @field_validator('skills','domains','locations')
    @classmethod
    def clean_list(cls, values):
        if any(not value.strip() or len(value)>100 for value in values):
            raise ValueError('List values must be nonempty and at most 100 characters')
        return list(dict.fromkeys(v.strip() for v in values))

class AnnouncementInput(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=180)
    domain: str = Field(default='Software Development', max_length=80)
    location: str = Field(default='Bengaluru', min_length=1, max_length=120)
    work_mode: Literal['On-site','Remote','Hybrid'] = 'On-site'
    stipend: int = Field(default=0, ge=0, le=10000000)
    duration_months: int = Field(default=3, ge=1, le=24)
    min_cgpa: float = Field(default=0, ge=0, le=10)
    eligible_year: int = Field(default=3, ge=1, le=5)
    eligible_branch: str = Field(default='Any', max_length=100)
    experience_months: int = Field(default=0, ge=0, le=240)
    skills: list[str] = Field(default_factory=list, max_length=100)
    description: str = Field(default='', max_length=20000)
    application_url: str = Field(default='', max_length=2000)
    deadline: str | None = None
    oa: str | None = None
    ppt: str | None = None
    @field_validator('application_url')
    @classmethod
    def safe_url(cls,value):
        if value and (urlparse(value).scheme not in ('https','http') or not urlparse(value).netloc):
            raise ValueError('Application URL must be an absolute http(s) URL')
        return value
    @field_validator('deadline','oa','ppt')
    @classmethod
    def date_valid(cls,value):
        if value:
            datetime.fromisoformat(value.replace('Z','+00:00'))
        return value
    @field_validator('skills')
    @classmethod
    def clean_skills(cls,values):
        if any(not v.strip() or len(v)>80 for v in values):
            raise ValueError('Skills must be nonempty and at most 80 characters')
        return list(dict.fromkeys(v.strip() for v in values))

class TextExtraction(BaseModel):
    text: str = Field(min_length=20, max_length=30000)
    use_ai: bool = False

class IngestionInput(BaseModel):
    announcement: AnnouncementInput
    source_text: str = Field(min_length=20, max_length=30000)
    extraction_mode: str = Field(default='Rules', max_length=40)

class ApplicationUpdate(BaseModel):
    status: Literal['Draft','Applied','Assessment','Interview','Offer','Rejected','Withdrawn'] | None = None
    cover_letter: str | None = Field(default=None, max_length=15000)
    notes: str | None = Field(default=None, max_length=5000)
