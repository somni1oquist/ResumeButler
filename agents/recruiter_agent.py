import os
from datetime import datetime
from kernel import get_kernel
from utils import IntentDetector, load_prompt, get_profile
from . import BaseAgent
from plugins import RecruiterPlugin, get_tool_output
from constants import ServiceIDs, Intent
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments


class RecruiterAgent(ChatCompletionAgent, BaseAgent):
    """Agent to process resumes and generate match reports based on job descriptions."""
    intent_detector: IntentDetector = IntentDetector()

    def __init__(self, name: str = "RecruiterAgent", kernel=None, instructions: str = ""):
        super().__init__(name=name, kernel=kernel, instructions=instructions)

        # Initialize Azure OpenAI service for resume processing
        if not self.kernel.services.get(ServiceIDs.AZURE_HR_SERVICE):
            az_hr_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_HR_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            recruiter_plugin = RecruiterPlugin()
            self.kernel.add_plugin(recruiter_plugin, plugin_name="RecruiterPlugin")
            self.kernel.add_service(az_hr_service)

    @classmethod
    async def create(cls, name: str = "RecruiterAgent"):
        """Async factory method to create RecruiterAgent with loaded instructions."""
        kernel, _ = get_kernel()
        instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now()))
        if not instruction:
            raise ValueError("Failed to load recruiter agent instructions.")

        return cls(name=name, kernel=kernel, instructions=instruction)

    async def process(self, prompt: str, **kwargs) -> dict | str:
        """Process resume and job description to generate match report."""
        # Unpack additional arguments
        if "user_profile" in kwargs:
            user_profile = kwargs.get("user_profile")
            new_instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now(), user_profile=user_profile))
            self.instructions = new_instruction if new_instruction else self.instructions

        try:
            response = await self.get_response(messages=prompt)
            self.thread = response.thread
            if get_tool_output(self.thread):
                tool_output = get_tool_output(self.thread)
                return {"tool_output": tool_output}
            return str(response.message)
        except Exception as e:
            raise ValueError(f"Error processing request: {e}")
        
    async def ask(self, data: dict) -> dict | str:
        """Process user input and return a response."""
        from agents.writer_agent import WriterAgent

        profile = get_profile(data)
        prompt = data.get("user_input", "User input not provided.")

        # @TODO: Refactor intent detection to use a more robust method
        # For now, we use the intent detector to determine the user's intent
        intent = self.intent_detector.detect_intent(prompt)
        if intent == Intent.REWRITE_RESUME:
            prompt_with_intent = f"Rewrite the resume based on the following input: {prompt}"
            writer_agent = WriterAgent(kernel=self.kernel)
            response = await writer_agent.process(prompt_with_intent, **{"user_profile": profile})
            return response
        elif intent == Intent.REVIEW_RESUME:
            response = await self.process(prompt, **{"user_profile": KernelArguments(user_profile=profile)})
        else:
            response = await self.process(prompt)

        return response