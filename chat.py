import asyncio
from kernel import get_kernel, get_basic_args, get_prompt
from user_profile import UserProfile
from streamlit.runtime.uploaded_file_manager import UploadedFile
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
from utils import detect_exit_intent, ai_detect_exit_intent


user_profile = UserProfile()
chat_history = ChatHistory()
async def chat(user_question: str | None = None) -> bool | str:
    """Interact with the Recruiter AI."""
    kernel, request_settings = get_kernel()
    
    # Ensure we have the necessary data loaded
    if not user_profile.resume or not user_profile.jd:
        basic_args = get_basic_args(user_profile=user_profile)
        if basic_args is None:
            print("❌ Failed to load resume and job description.")
            return False
    # Render the system prompt with user profile data
    system_args = KernelArguments(
        resume=user_profile.resume,
        jd=user_profile.jd,
        match_report=user_profile.match_report
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
        
        print(f"\n🤖 Recruiter:")
        print("-" * 30)
        print(response_text)
        print("-" * 30)
        return response_text
    else:
        print("❌ Failed to generate HR response.")
        return False

async def match(resume_file: UploadedFile, jd_text: str) -> str:
    """Generate a match report between the resume and job description."""
    kernel, request_settings = get_kernel()
    user_profile.resume_file = resume_file
    user_profile.jd = jd_text.strip() if jd_text else None
    match_args = get_basic_args(user_profile=user_profile)
    match_prompt = await get_prompt("match", match_args)
    if match_prompt:
        response = await kernel.invoke_prompt(match_prompt, settings=request_settings)
        user_profile.match_report = str(response)
        return str(response)
    return "❌ Failed to generate match report."

async def main():
    print("🚀 Starting Resume Service with Semantic Kernel...")
    
    # Step 1: Generate match report using semantic kernel
    basic_args = get_basic_args(user_profile=user_profile)
    if basic_args is None:
        print("❌ Failed to load resume and job description.")
        return
    kernel, _ = get_kernel()
    match_prompt = await get_prompt("match", basic_args)
    if match_prompt:
        print("📊 Generating Match Report...")
        response = await kernel.invoke_prompt(match_prompt)
        match_report = str(response)
        
        # Store match report in user profile for persistence
        user_profile.match_report = match_report
        
        print("📊 Match Report:")
        print("=" * 50)
        print(match_report)
        print("=" * 50)
        
        # Step 2: Interactive HR chat with kernel
        print("\n🤖 Senior Recruiter Ready for Consultation!")
        print("💬 Ask questions about your resume, job description, or match report.")
        print("Type 'quit' or 'exit' to end the chat.\n")
        
        # Interactive chat loop
        while True:
            try:
                exit_response = "👋 Thanks for using the Resume Service! Good luck with your application!"
                user_input = input("\nUser:> ").strip()

                if is_exit := detect_exit_intent(user_input) is None:
                    is_exit = await ai_detect_exit_intent(user_input, chat_history)
                if is_exit:
                    print(exit_response)
                    break

                if user_input:
                    # Call the chat function with user input
                    await chat(user_input)
                else:
                    print("Please enter a question or 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\n👋 Thanks for using the Resume Service!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
                
    else:
        print("❌ Failed to render the match prompt.")

if __name__ == "__main__":
    asyncio.run(main())