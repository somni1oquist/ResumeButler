import os
from typing import Any
from datetime import datetime
from kernel import get_kernel
from utils import load_prompt
from . import BaseAgent
from plugins import RevisionPlugin, get_tool_output
from constants import ServiceIDs
from user_profile import UserProfile
from semantic_kernel.agents import ChatCompletionAgent, AgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments


class WriterAgent(ChatCompletionAgent, BaseAgent):
    """Agent to assist with writing tasks and content generation."""
    thread: AgentThread | None = None

    def __init__(self, name: str = "WriterAgent", kernel=None, instructions: str = ""):
        super().__init__(name=name, kernel=kernel, instructions=instructions)

        # Initialize Azure OpenAI service for resume processing
        if not self.kernel.services.get(ServiceIDs.AZURE_WRITER_SERVICE):
            az_writer_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_WRITER_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            revision_plugin = RevisionPlugin()
            self.kernel.add_service(az_writer_service)
            self.kernel.add_plugin(revision_plugin, plugin_name="RevisionPlugin")

    @classmethod
    async def create(cls, name: str = "WriterAgent"):
        """Async factory method to create WriterAgent with loaded instructions."""
        kernel, _ = get_kernel()
        instruction = await load_prompt("writer_agent", KernelArguments(now=datetime.now()))
        if not instruction:
            raise ValueError("Failed to load writer agent instructions.")

        return cls(name=name, kernel=kernel, instructions=instruction)

    async def process(self, prompt: str, thread: AgentThread | None, **kwargs) -> Any:
        """Process resume and job description to generate match report."""
        # Unpack additional arguments
        if "user_profile" in kwargs:
            user_profile: UserProfile | None = kwargs.get("user_profile")
            if user_profile:
                new_instruction = await load_prompt("writer_agent", KernelArguments(
                    now=datetime.now(), resume=user_profile.resume, jd=user_profile.jd
                ))
                self.instructions = new_instruction if new_instruction else self.instructions

        try:
            response = await self.get_response(messages=prompt, thread=thread)
            self.thread = response.thread

            print("RecruiterAgent finished processing.")

            if get_tool_output(self.thread):
                tool_output = get_tool_output(self.thread)
                return {"tool_output": tool_output}, self.thread
            return response, self.thread
        except Exception as e:
            raise ValueError(f"Error processing request: {e}")
