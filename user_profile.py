from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    # Existing fields for resume analysis
    resume: str | None = Field(default=None, description="Parsed resume content")
    jd: str | None = Field(default=None, description="Job description content")
    match_report: str | None = Field(default=None, description="Match report")
    
    # New fields for resume generation
    name: str | None = Field(default=None, description="Full name")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    location: str | None = Field(default=None, description="Location (city, state/country)")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL")
    summary: str | None = Field(default=None, description="Professional summary")
    experience: str | None = Field(default=None, description="Work experience details")
    education: str | None = Field(default=None, description="Education details")
    skills: str | None = Field(default=None, description="Technical and soft skills")
    certifications: str | None = Field(default=None, description="Certifications")
    projects: str | None = Field(default=None, description="Projects")
    
    # Agent state fields
    agent_mode: str | None = Field(default=None, description="Current agent mode (create, rewrite, chat, export)")
    target_role: str | None = Field(default=None, description="Target job role")
    generated_resume: str | None = Field(default=None, description="Generated resume content")
    last_question: str | None = Field(default=None, description="Last question asked by agent")
    
    def get_missing_essential_fields(self) -> list[str]:
        """Get list of missing essential fields for resume generation"""
        essential_fields = ['name', 'email', 'phone', 'summary', 'experience', 'education', 'skills']
        missing = []
        for field in essential_fields:
            if getattr(self, field) is None:
                missing.append(field)
        return missing
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage for resume generation"""
        all_fields = ['name', 'email', 'phone', 'location', 'linkedin', 'summary', 
                     'experience', 'education', 'skills', 'certifications', 'projects']
        completed = sum(1 for field in all_fields if getattr(self, field) is not None)
        return (completed / len(all_fields)) * 100
    
    def is_ready_for_generation(self) -> bool:
        """Check if profile has enough information for resume generation"""
        essential_fields = ['name', 'email', 'phone', 'summary', 'experience', 'education', 'skills']
        return all(getattr(self, field) is not None for field in essential_fields)