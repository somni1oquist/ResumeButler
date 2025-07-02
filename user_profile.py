from pydantic import BaseModel, Field
from streamlit.runtime.uploaded_file_manager import UploadedFile


class UserProfile(BaseModel):
    resume_file: UploadedFile | None = Field(
        default=None, description="Uploaded resume file in PDF or DOCX format"
    )
    resume: str | None = Field(default=None, description="Parsed resume content")
    jd: str | None = Field(default=None, description="Job description content")
    match_report: str | None = Field(default=None, description="Match report")