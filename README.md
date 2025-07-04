# Resume Butler

This system combines resume-job matching analysis with interactive HR consultation and **AI-powered resume creation** using Semantic Kernel and Azure OpenAI.

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

### 🚀 **NEW: AI Agent for Resume Creation**
- **Goal-driven resume creation** from scratch
- **Intelligent information collection** through natural conversation
- **Smart resume rewriting** and enhancement
- **Multi-format export** (Markdown, HTML, DOCX, PDF*)
- **Intent detection** for seamless workflow switching

## Files Overview

### YAML Templates
- **`prompts/match.yaml`**: Template for generating detailed match reports
- **`prompts/hr_chat.yaml`**: Template for consultation
- **`prompts/hr_system.yaml`**: Template for Recruiter
- **`prompts/agent_intent.yaml`**: ✨ **NEW** - Intent detection for agent workflows
- **`prompts/resume_generation.yaml`**: ✨ **NEW** - Resume generation from user profile
- **`prompts/field_collection.yaml`**: ✨ **NEW** - Dynamic information collection

### Python Scripts
- **`match.py`**: Match resume against given job description
- **`utils.py`**: Resume parsing utilities
- **`agent.py`**: ✨ **NEW** - AI agent for goal-driven resume creation
- **`export.py`**: ✨ **NEW** - Multi-format resume export functionality
- **`user_profile.py`**: ✨ **ENHANCED** - Extended with resume generation fields

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
```

## Quick Start

### Run Script
```bash
streamlit run app.py
```

## 🤖 Agent Features

### Smart Intent Detection
The AI agent automatically recognizes when you want to:
- Create a new resume from scratch
- Improve an existing resume  
- Export or download your resume
- Have a general career conversation

### Dynamic Information Collection
Instead of filling out forms, just have a conversation:
- "My name is John Doe and I'm a software engineer"
- "I have 5 years of experience at Google and Microsoft"
- "I graduated from Stanford with a Computer Science degree"

The agent extracts structured information and asks follow-up questions for anything missing.

### Professional Resume Generation
Generates resumes with:
- ATS-friendly formatting
- Action verb optimization
- Quantifiable achievements
- Industry-specific customization
- Professional summary generation

### Multi-Format Export
Export your resume in the format you need:
```python
from export import ResumeExporter

exporter = ResumeExporter()
markdown_path, content = exporter.export_markdown(resume)
html_path, content = exporter.export_html(resume)
docx_path, content = exporter.export_docx(resume)
```

## How It Works

### Step 1: Choose Your Workflow
The Resume Butler now supports multiple modes:

#### 🔍 **Analysis Mode** (Original)
- Upload your resume and job description
- Get detailed match analysis with percentage scoring
- Receive specific improvement recommendations

#### 🚀 **Creation Mode** (NEW)
- Click "Create New Resume" or say "create resume"
- AI agent guides you through information collection
- Generate a professional resume from scratch

#### 🔄 **Enhancement Mode** (NEW)  
- Upload existing resume and choose "Improve Resume"
- AI agent analyzes and rewrites for better impact
- Maintains your content while improving structure and language

### Step 2: Agent-Driven Interaction
The AI agent intelligently:
- **Detects your intent** (create, improve, analyze, export)
- **Collects missing information** through natural conversation
- **Tracks completion progress** with visual feedback
- **Guides you toward your goal** step by step

### Step 3: Professional Resume Generation
Using advanced prompt templates, the system:
- Generates structured, ATS-friendly resumes
- Customizes content for target roles
- Follows professional formatting standards
- Includes quantifiable achievements and action verbs

### Step 4: Export & Share
Choose from multiple export formats:
- **Markdown**: Perfect for version control and editing
- **HTML**: Web-ready with professional styling  
- **DOCX**: Microsoft Word compatible
- **PDF**: Print-ready professional documents*

*PDF export requires additional dependencies

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

### 🚀 Agent-Powered Resume Creation
1. Open Resume Butler
2. Click "🚀 Create New Resume" or type "create resume"
3. Follow the AI agent's questions to provide your information
4. Review and export your generated resume

### 🔄 Resume Enhancement  
1. Upload your existing resume
2. Click "🔄 Improve Resume" or type "rewrite resume"
3. AI agent analyzes and suggests improvements
4. Get an enhanced version with better impact

### 🔍 Traditional Analysis + Chat
1. Upload resume and job description  
2. Click "Generate Match Report"
3. Ask specific questions about improvements
4. Get personalized career advice

### 💬 General Career Consultation
- Ask: "What should I include in a good resume?"
- Ask: "How do I prepare for a software engineer interview?"  
- Ask: "What skills are in demand for my field?"