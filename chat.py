from kernel import get_kernel
from utils import load_prompt
from utils import get_parser_manager
from streamlit.runtime.uploaded_file_manager import UploadedFile
from user_profile import UserProfile
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory


user_profile = UserProfile()
chat_history = ChatHistory()
_parser = get_parser_manager()
@DeprecationWarning
async def chat(user_question: str | None = None) -> bool | str:
    """Interact with the Recruiter AI."""
    kernel, request_settings = get_kernel()
    
    # Render the system prompt with user profile data
    system_args = KernelArguments(
        resume=user_profile.resume,
        jd=user_profile.jd,
        match_report=user_profile.match_report
    )
    sys_prompt = await load_prompt("hr_system", system_args)
    chat_history.system_message = sys_prompt

    # Render the chat prompt with user question and chat history
    chat_args = KernelArguments(
        user_question=user_question,
        chat_history=chat_history
    )
    chat_prompt = await load_prompt("hr_chat", chat_args)

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
        print("Failed to generate HR response.")
        return False

@DeprecationWarning
async def match(resume_file: UploadedFile, jd_text: str) -> str:
    """Generate a match report between the resume and job description."""
    kernel, request_settings = get_kernel()
    user_profile.jd = jd_text.strip() if jd_text else None

    # Load and parse the resume file
    try:
        user_profile.resume = _parser.parse_document(resume_file)
    except (FileNotFoundError, IOError):
        print(f"Error loading resume. Please check the file.")
        user_profile.resume = None

    # Prepare for the match report generation
    match_args = KernelArguments(
        resume=user_profile.resume,
        jd=user_profile.jd
    )
    match_prompt = await load_prompt("match", match_args)
    
    if match_prompt:
        response = await kernel.invoke_prompt(match_prompt, settings=request_settings)
        user_profile.match_report = str(response)
        return str(response)
    return "❌ Failed to generate match report."