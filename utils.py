from kernel import get_kernel, get_prompt
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
import re


def parse_resume(file) -> str:
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file.name)
    file.seek(0)
    if mime_type == "application/pdf":
        return _parse_pdf(file)
    elif mime_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       "application/msword"):
        return _parse_docx(file)
    elif mime_type == "text/plain":
        return _parse_txt(file)
    else:
        raise ValueError("Unsupported file type")

def _parse_pdf(file) -> str:
    """
    Parse PDF files and return their content as Markdown text.
    """
    import pymupdf4llm, pymupdf
    file_bytes = file.read()
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        md_text = pymupdf4llm.to_markdown(doc)
        if not md_text.strip():
            raise ValueError("Failed to extract text from PDF")
        return md_text

def _parse_docx(file) -> str:
    """
    Parse DOCX files and return their content as text.
    """
    import docx2txt
    return docx2txt.process(file)

def _parse_txt(file) -> str:
    """
    Parse plain text files and return their content as a string.
    """
    return file.read().decode('utf-8').strip()

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

async def ai_detect_exit_intent(user_input: str, chat_history: ChatHistory) -> bool:
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