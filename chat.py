import asyncio
import re
from kernel import get_kernel, get_basic_args, get_prompt
from user_profile import UserProfile
from streamlit.runtime.uploaded_file_manager import UploadedFile
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory


user_profile = UserProfile()
chat_history = ChatHistory()
_agent = None  # Lazy initialization


def get_agent():
    """Get agent instance with lazy initialization"""
    global _agent
    if _agent is None:
        try:
            from agent import ResumeButlerAgent
            _agent = ResumeButlerAgent(user_profile, chat_history)
        except Exception as e:
            print(f"Failed to initialize agent: {e}")
            _agent = None
    return _agent
async def chat(user_question: str | None = None) -> bool | str:
    """Interact with the Recruiter AI or Resume Agent."""
    # Try to get agent instance
    agent = get_agent()
    
    # Check if user wants to use agent mode
    if user_question and any(keyword in user_question.lower() for keyword in 
                           ['create resume', 'new resume', 'generate resume', 'build resume', 'rewrite resume', 'improve resume']):
        # Use agent mode
        if agent:
            try:
                response = await agent.process_message(user_question)
                return response
            except Exception as e:
                print(f"Agent processing failed: {e}")
                return f"I'd love to help you create a resume, but I need to be configured with Azure OpenAI credentials first. In the meantime, I can help with general career questions!"
        else:
            return f"I'd love to help you create a resume, but I need to be configured with Azure OpenAI credentials first. In the meantime, I can help with general career questions!"
    
    # Check if we're already in agent mode
    if agent and user_profile.agent_mode and user_profile.agent_mode != 'chat':
        try:
            response = await agent.process_message(user_question)
            return response
        except Exception as e:
            print(f"Agent processing failed: {e}")
            # Fall back to regular chat
    
    # Regular HR chat mode - only if we have resume or jd data
    if user_profile.resume or user_profile.jd:
        try:
            kernel, request_settings = get_kernel()
            
            # Render the system prompt with user profile data
            system_args = KernelArguments(
                resume=user_profile.resume or "",
                jd=user_profile.jd or "",
                match_report=user_profile.match_report or ""
            )
            sys_prompt = await get_prompt("hr_system", system_args)
            chat_history.system_message = sys_prompt

            # Render the chat prompt with user question and chat history
            chat_args = KernelArguments(
                user_question=user_question,
                chat_history=chat_history
            )
            chat_prompt = await get_prompt("hr_chat", chat_args)

            if chat_prompt:
                # Invoke the kernel with the rendered prompt
                response = await kernel.invoke_prompt(
                    prompt=chat_prompt,
                    settings=request_settings
                )
                response_text = str(response)
                # Add user and assistant messages to chat history for persistence
                chat_history.add_user_message(user_question)
                chat_history.add_assistant_message(response_text)
                return response_text
            else:
                return "I'm having trouble generating a response. Please try again."
        except Exception as e:
            print(f"Regular chat failed: {e}")
            return "I'm having trouble generating a response. Please try again."
    else:
        # No resume or JD data, provide helpful guidance
        return """I'm ready to help you! Here's what I can do:

🚀 **Create a new resume** - Just say "create resume" and I'll guide you through building one from scratch
🔍 **Analyze your resume** - Upload your resume and job description for detailed analysis
💼 **Career advice** - Ask me about job searching, interview tips, or career guidance

What would you like to do today?"""

async def match(resume_file: UploadedFile, jd_text: str) -> str:
    """Generate a match report between the resume and job description."""
    kernel, request_settings = get_kernel()
    user_profile.jd = jd_text.strip() if jd_text else None
    match_args = get_basic_args(user_profile=user_profile, resume_file=resume_file)
    match_prompt = await get_prompt("match", match_args)
    if match_prompt:
        response = await kernel.invoke_prompt(match_prompt, settings=request_settings)
        user_profile.match_report = str(response)
        return str(response)
    return "❌ Failed to generate match report."