import os
from datetime import datetime
from typing import override, Any, Callable, Awaitable, AsyncIterable
from kernel import get_kernel
from utils import load_prompt
from . import BaseAgent
from plugins import get_tool_output
from constants import ServiceIDs
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentThread, AgentResponseItem
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent, AuthorRole


class RecruiterAgent(ChatCompletionAgent, BaseAgent):
    """Agent to analyse resumes and generate match reports based on job descriptions."""

    def __init__(self, name: str = "RecruiterAgent", kernel=None, instructions: str = "You are ResumeAgent — an experienced recruiter and HR specialist helping job seekers improve their resumes and career outcomes."):
        super().__init__(name=name, kernel=kernel, instructions=instructions,
                         description="An AI assistant specialized in resume analysis and job matching.")

        # Initialize Azure OpenAI service for resume processing
        if not self.kernel.services.get(ServiceIDs.AZURE_HR_SERVICE):
            az_hr_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_HR_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            self.kernel.add_service(az_hr_service)

    @classmethod
    async def create(cls, kernel: Kernel, name: str = "RecruiterAgent"):
        """Async factory method to create RecruiterAgent with loaded instructions."""
        instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now()))
        if not instruction:
            raise ValueError("Failed to load recruiter agent instructions.")

        return cls(name=name, kernel=kernel, instructions=instruction)

    @override
    async def invoke_stream(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:

        if not self.arguments:
            self.arguments = KernelArguments(resume="Not provided.", jd="Not provided.", now=datetime.now())
        else:
            self.arguments.update(now=datetime.now())

        new_instruction = await load_prompt("recruiter_agent", self.arguments)
        self.instructions = new_instruction if new_instruction else self.instructions

        input_message = None
        if isinstance(messages, str):
            input_message = messages
        elif isinstance(messages, list) and messages:
            input_message = messages[-1].content if isinstance(messages[-1], ChatMessageContent) else messages[-1]
        elif isinstance(messages, ChatMessageContent):
            input_message = messages.content
        else:
            input_message = ""

        async for item in super().invoke_stream(
            messages=[ChatMessageContent(role=AuthorRole.USER, content=input_message)],
            thread=thread,
            on_intermediate_message=on_intermediate_message,
            kernel=self.kernel,
        ):
            yield item

    async def process(self, prompt: str, thread: AgentThread | None, **kwargs):
        """Process resume and job description to generate match report."""
        new_instruction = await load_prompt("recruiter_agent", KernelArguments(now=datetime.now(), user_profile=self.arguments))
        self.instructions = new_instruction if new_instruction else self.instructions

        try:
            response = await self.get_response(messages=prompt, thread=thread)
            self._thread = response.thread

            if get_tool_output(self._thread):
                tool_output = get_tool_output(self._thread)
                return {"tool_output": tool_output}, self._thread
            return response, self._thread
        except Exception as e:
            raise ValueError(f"Error processing request: {e}")