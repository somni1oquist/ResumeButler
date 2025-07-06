import os
from kernel import get_kernel, load_prompt
from document_parser import get_parser_manager
from . import BaseAgent
from user_profile import UserProfile
from tools import RevisionPlugin
from constants import ServiceIDs
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments


_parser = get_parser_manager()

class ResumeAgent(ChatCompletionAgent, BaseAgent):
    """Agent to process resumes and generate match reports based on job descriptions."""

    def __init__(self, name: str = "ResumeAgent", kernel=None, instructions: str = ""):
        super().__init__(name=name, kernel=kernel, instructions=instructions)

        # Initialize Azure OpenAI service for resume processing
        if not self.kernel.services.get(ServiceIDs.AZURE_RESUME_SERVICE):
            az_resume_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_RESUME_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            revision_plugin = RevisionPlugin()
            self.kernel.add_service(az_resume_service)
            self.kernel.add_plugin(revision_plugin, plugin_name="RevisionPlugin")

    @classmethod
    async def create(cls, name: str = "ResumeAgent"):
        """Async factory method to create ResumeAgent with loaded instructions."""
        kernel, _ = get_kernel()
        instruction = await load_prompt("resume_agent")
        if not instruction:
            raise ValueError("Failed to load resume agent instructions.")
        
        return cls(name=name, kernel=kernel, instructions=instruction)

    async def process(self, prompt: str, thread: ChatHistoryAgentThread | None = None, **kwargs) -> str:
        """Process resume and job description to generate match report."""
        if not thread:
            thread = ChatHistoryAgentThread()
        # Unpack additional arguments
        if "user_profile" in kwargs:
            new_instruction = await load_prompt("resume_agent", kwargs.get("user_profile"))
            self.instructions = new_instruction if new_instruction else self.instructions

        try:
            response = await self.get_response(messages=prompt, thread=thread)
            return str(response)
        except Exception as e:
            return f"Error processing request: {e}"
        
    async def ask(self, data: dict, thread: ChatHistoryAgentThread | None = None) -> str:
        """Process user input and return a response."""
        profile = self.get_profile(data)
        prompt = data.get("user_input", "User input not provided.")
        if profile:
            response = await self.process(prompt, thread, **{"user_profile": KernelArguments(user_profile=profile)})
        else:
            response = await self.process(prompt, thread)
        return response

    async def get_match_report(self, data: dict, thread: ChatHistoryAgentThread | None) -> str:
        """Generate a match report between the resume and job description."""
        profile = self.get_profile(data)
        match_args = KernelArguments(resume=profile.resume, jd=profile.jd)
        match_prompt = await load_prompt("match", match_args)
        # Process with user profile if match prompt is found
        if match_prompt and profile:
            response = await self.process(match_prompt, thread, **{"user_profile": KernelArguments(user_profile=profile)})
            return response
        # Process without user profile if match prompt is found
        elif match_prompt:
            response = await self.process(match_prompt, thread)
            return response
        return "No match template found."

    def get_profile(self, data: dict) -> UserProfile:
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