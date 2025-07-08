"""Constants for the Resume Butler application."""

# Kernel Service IDs
class ServiceIDs:
    AZURE_HR_SERVICE = "az_hr_service"
    AZURE_WRITER_SERVICE = "az_writer_service"
    AZURE_CONTROL_SERVICE = "az_control_service"

# Intent Detection
class Intent:
    UNKNOWN = "unknown"
    REVIEW_RESUME = "ReviewResume"
    REWRITE_RESUME = "RewriteResume"
    CONSULT = "Consult"

# File Types
SUPPORTED_RESUME_TYPES = ["pdf", "docx", "txt"]