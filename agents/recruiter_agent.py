import os
from datetime import datetime
from kernel import get_kernel
from utils import load_prompt
from . import BaseAgent
from plugins import RevisionPlugin, RecruiterPlugin, get_tool_output
from constants import ServiceIDs
from semantic_kernel.agents import ChatCompletionAgent, AgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments


class RecruiterAgent(ChatCompletionAgent, BaseAgent):
    """Agent to analyse resumes and generate match reports based on job descriptions."""
    thread: AgentThread | None = None

    def __init__(self, name: str = "RecruiterAgent", kernel=None, instructions: str = "You are ResumeAgent — an experienced recruiter and HR specialist helping job seekers improve their resumes and career outcomes."):
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
            rev = RevisionPlugin()
            self.kernel.add_plugin(recruiter_plugin, plugin_name="RecruiterPlugin")
            self.kernel.add_plugin(rev, plugin_name="RevisionPlugin")
            self.kernel.add_service(az_hr_service)

    @classmethod
    async def create(cls, name: str = "RecruiterAgent"):
        """Async factory method to create RecruiterAgent with loaded instructions."""
        kernel, _ = get_kernel()
        instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now()))
        if not instruction:
            raise ValueError("Failed to load recruiter agent instructions.")

        return cls(name=name, kernel=kernel, instructions=instruction)

    async def process(self, prompt: str, thread: AgentThread | None, **kwargs):
        """Process resume and job description to generate match report."""
        # Unpack additional arguments
        if "user_profile" in kwargs:
            user_profile = kwargs.get("user_profile")
            new_instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now(), user_profile=user_profile))
            self.instructions = new_instruction if new_instruction else self.instructions

        try:
            response = await self.get_response(messages=prompt)
            self.thread = response.thread

            print("RecruiterAgent finished processing.")

            if get_tool_output(self.thread):
                tool_output = get_tool_output(self.thread)
                return {"tool_output": tool_output}, self.thread
            return response, self.thread
        except Exception as e:
            raise ValueError(f"Error processing request: {e}")