from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    resume: str | None = Field(default=None, description="Parsed resume content")
    jd: str | None = Field(default=None, description="Job description content")