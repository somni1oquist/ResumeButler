from user_profile import UserProfile
from document_parser import get_parser_manager


_parser = get_parser_manager()

def get_profile(data: dict) -> UserProfile:
    """Extract user profile information from the provided data."""
    user_profile = UserProfile()
    user_profile.resume = data.get("resume")
    user_profile.jd = data.get("jd")

    if data.get("resume_file"):
        resume_file = data.get("resume_file")
        if resume_file is not None:
            resume = _parser.parse_document(resume_file)
            user_profile.resume = resume
    
    return user_profile