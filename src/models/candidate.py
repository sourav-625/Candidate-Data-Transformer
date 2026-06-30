from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Candidate(BaseModel):
    candidate_id: Optional[str] = None

    full_name: Optional[str] = None

    emails: List[str] = Field(default_factory=list)

    phones: List[str] = Field(default_factory=list)

    location: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "country": None,
            "state": None,
            "city": None
        }
    )

    links: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "github": None,
            "linkedin": None,
            "portfolio": None
        }
    )

    headline: Optional[str] = None

    years_experience: Optional[float] = None

    skills: List[str] = Field(default_factory=list)

    experience: List[Experience] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)

    provenance: Dict[str, List[str]] = Field(default_factory=dict)

    overall_confidence: Optional[float] = None

    warnings: List[str] = Field(default_factory=list)