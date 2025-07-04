# Resume Butler

This system combines resume-job matching analysis with interactive HR consultation using Semantic Kernel and Azure OpenAI.

## Features

### 🔍 Resume Analysis
- Automated matching between resumes and job descriptions
- Skills gap analysis
- Match percentage scoring
- Keyword extraction and comparison
- Enhanced document structure parsing with Azure Document Intelligence
- Automatic fallback to basic parsing methods when Azure services aren't available

### 🤖 Recruiter AI Consultation
- Interactive career guidance
- Interview preparation tips
- Resume improvement suggestions
- Personalised feedback
- Improved context understanding from structured document parsing

## Files Overview

### YAML Templates
- **`prompts/match.yaml`**: Template for generating detailed match reports
- **`prompts/hr_chat.yaml`**: Template for consultation
- **`prompts/hr_system.yaml`**: Template for Recruiter

### Python Scripts
- **`match.py`**: Match resume against given job description
- **`document_parser.py`**: Advanced document parsing with Azure Document Intelligence integration

## Setup

- `python -m venv .venv`
- `source .venv/bin/activate` OR `.\.venv\Scripts\activate`
- `pip install -r requirements.txt`
- Create `.env` file:
```
GLOBAL_LLM_SERVICE="azure_openai"
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://..."
AZURE_OPENAI_DEPLOYMENT_NAME="..."

# Optional: For enhanced document parsing with Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://..."
AZURE_DOCUMENT_INTELLIGENCE_API_KEY="..."
```

**Note:** Azure Document Intelligence integration provides enhanced document structure parsing. If not configured, the system will fall back to basic PDF/DOCX parsing methods.

## Quick Start

### Run Script
```bash
streamlit run app.py
```

## How It Works

### Step 1: Match Report Generation
The system uses `match.yaml` to analyze your resume against a job description:
- Calculates match percentage
- Identifies matched and missing skills
- Compares keywords
- Assesses experience and education fit

### Step 2: Recruiter Consultation
The `hr_chat.yaml` template enables:
- Interactive Q&A based on the match report
- Personalised career advice
- Specific improvement recommendations
- Interview preparation guidance

## Key Integration Features

### Flexible Input Handling
The Recruiter AI can work with:
- Pre-generated match reports
- Direct resume and job description inputs
- General career questions

### Enhanced Conversation Flow
- Initial match analysis provides context
- Recruiter AI references specific findings
- Continuous conversation capability
- Contextual career guidance

## Usage Examples

### Automated Analysis + Chat
1. Load resume and job description
2. Generate comprehensive match report
3. Ask specific questions about improvements
4. Get personalized career advice

### Direct HR Consultation
- Skip match report generation
- Ask general career questions
- Get industry insights
- Receive interview tips