from typing import Optional, Literal
from pydantic import BaseModel, Field

class DogRegistration(BaseModel):
    name: str = Field(default="Unnamed", max_length=80)
    area: str = Field(min_length=1, max_length=120)
    age_group: Optional[Literal["Puppy", "Adult", "Senior", "Unknown"]] = "Unknown"
    sex: Optional[Literal["Male", "Female", "Unknown"]] = "Unknown"
    vaccination_status: Literal["Anti-rabies verified", "Due", "Unknown"] = "Unknown"
    vaccination_date: Optional[str] = None
    sterilization_status: Literal["Spayed", "Neutered", "Not done", "Unknown"] = "Unknown"
    distinguishing_marks: Optional[str] = Field(default=None, max_length=500)
    caregiver_name: Optional[str] = Field(default=None, max_length=100)
    caregiver_contact: Optional[str] = Field(default=None, max_length=40)
    care_notes: Optional[str] = Field(default=None, max_length=1000)

class DogRecord(DogRegistration):
    dog_id: str
    created_at: str
    updated_at: str
    caregiver_token: str
    qr_file: Optional[str] = None
    embedding_status: str = "not_available"

class MatchResult(BaseModel):
    status: Literal["match_found", "low_confidence", "no_match", "quality_retry"]
    message: str
    dog: Optional[DogRecord] = None
    similarity: Optional[float] = None
    note: str = "Similarity is a prototype score, not validated recognition accuracy."
