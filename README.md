# Resume Butler

This system combines resume-job matching analysis with interactive HR consultation using Semantic Kernel and Azure OpenAI.

## Features

### 🔍 Resume Analysis
- Automated matching between resumes and job descriptions
- Skills gap analysis
- Match percentage scoring
- Keyword extraction and comparison

### 🤖 Recruiter AI Consultation
- Interactive career guidance
- Interview preparation tips
- Resume improvement suggestions
- Personalised feedback

## Files Overview

### YAML Templates
- **`prompts/match.yaml`**: Template for generating detailed match reports
- **`prompts/hr_chat.yaml`**: Template for consultation
- **`prompts/hr_system.yaml`**: Template for Recruiter

### Python Scripts
- **`match.py`**: Match resume against given job description
- **`utils.py`**: Resume parsing utilities

## Setup

- `python -m venv .venv`
- Activate virtual environment
- `pip install -r requirements.txt` OR `pip install -U semantic-kernel dotenv pymupdf4llm docx2txt pyyaml`
- Create `.env` file:
```
GLOBAL_LLM_SERVICE="azure_openai"
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://..."
AZURE_OPENAI_DEPLOYMENT_NAME="..."
```

## Quick Start

### Run Script
```bash
python chat.py
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