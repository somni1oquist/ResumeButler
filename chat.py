import asyncio
from kernel import get_kernel, get_args, get_prompt
from user_profile import UserProfile
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
import re


user_profile = UserProfile()
chat_history = ChatHistory()

def detect_exit_intent(user_input: str) -> bool | None:
    """Detect if the user wants to exit the chat based on various signals. None if short affirmative response."""
    if not user_input:
        return False
    
    text = user_input.lower().strip()
    
    # 1. Direct exit commands
    exit_commands = [
        'quit', 'exit', 'bye', 'goodbye', 'stop', 'end', 'done', 
        'finish', 'close', 'terminate', 'cancel', 'leave', 'thanks',
        'ciao', 'farewell', 'adios', 'see ya', 'later', 'peace',
        'good night', 'goodnight', 'ttyl', 'talk to you later'
    ]
    if text in exit_commands:
        return True
    
    # 2. Check for phrases that indicate wanting to end
    exit_phrases = [
        r'\b(that\'s all|that is all|thats all)\b',
        r'\b(i\'m done|im done|i am done)\b',
        r'\b(thank you|thanks).*(bye|goodbye|done|enough|see you)\b',
        r'\b(bye|goodbye).*(thank|thanks|see you)\b',
        r'\b(no more|nothing else|that\'s it|thats it|nothing more)\b',
        r'\b(see you|talk to you|speak to you).*(later|soon|tomorrow)\b',
        r'\b(i have to go|got to go|gotta go|need to go)\b',
        r'\b(finish|finished).*(here|now|up|with this)\b',
        r'\b(enough for now|sufficient|all set)\b',
        r'\b(wrap up|wrapping up|wind up|winding up)\b',
        r'\b(call it a day|end this|end the chat)\b',
        r'\b(i\'m good|im good|all good).*(now|thanks|thank you)\b',
        r'\b(perfect|great|awesome).*(thanks|thank you|bye)\b'
    ]
    for pattern in exit_phrases:
        if re.search(pattern, text):
            return True
    
    # 3. Check for polite endings
    polite_endings = [
        r'\b(thank you|thanks).*(help|assistance|time)\b',
        r'\b(appreciate|grateful).*(help|time|assistance)\b',
        r'\b(perfect|great|excellent).*(thank|thanks)\b'
    ]
    for pattern in polite_endings:
        if re.search(pattern, text) and len(text.split()) <= 8:
            return True
    
    # 4. Check for very short affirmative responses that might indicate satisfaction
    short_responses = ['ok', 'okay', 'k', 'good', 'fine', 'sure', 'yep', 'yes']
    if len(text.split()) <= 2 and text in short_responses:
        return None
    
    return False

async def ai_detect_exit_intent(user_input: str) -> bool:
    """Use AI to detect if the user wants to exit the chat based on context and intent. None if detection fails."""
    try:
        kernel, request_settings = get_kernel()
        # Load the intent detection prompt
        recent_messages = chat_history.messages[-4:] if len(chat_history.messages) > 4 else chat_history.messages
        intent_args = KernelArguments(user_input=user_input, context=recent_messages) # Use last 4 messages for context
        intent_prompt = await get_prompt("exit_intent", intent_args)
        if not intent_prompt:
            raise ValueError("Exit intent prompt not found.")

        response = await kernel.invoke_prompt(
            prompt=intent_prompt,
            settings=request_settings
        )

        response_text = str(response).strip().upper()
        return response_text == "YES"

    except Exception as e:
        # Continue the chat to confirm exit intent
        print(f"⚠️ AI intent detection failed: {e}")
        return False

async def chat(user_question: str | None = None) -> bool | str:
    """Interact with the Recruiter AI."""
    kernel, request_settings = get_kernel()
    
    # Ensure we have the necessary data loaded
    if not user_profile.resume or not user_profile.jd:
        basic_args = get_args(user_profile=user_profile)
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

async def main():
    print("🚀 Starting Resume Service with Semantic Kernel...")
    
    # Step 1: Generate match report using semantic kernel
    basic_args = get_args(user_profile=user_profile)
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
                    is_exit = await ai_detect_exit_intent(user_input)
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