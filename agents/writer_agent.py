import os
from typing import Any, Callable, Awaitable, AsyncIterable, override
from datetime import datetime
from kernel import get_kernel
from utils import load_prompt
from . import BaseAgent
from plugins import get_tool_output
from constants import ServiceIDs
from user_profile import UserProfile
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentThread, AgentResponseItem
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent, AuthorRole


class WriterAgent(ChatCompletionAgent, BaseAgent):
    """Agent to assist with writing tasks and content generation."""

    def __init__(self, name: str = "WriterAgent", kernel=None, instructions: str = ""):
        super().__init__(name=name, kernel=kernel, instructions=instructions,
                         description="An AI assistant specialized in writing tasks, content generation, and resume processing.")

        # Initialize Azure OpenAI service for resume processing
        if not self.kernel.services.get(ServiceIDs.AZURE_WRITER_SERVICE):
            az_writer_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_WRITER_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            self.kernel.add_service(az_writer_service)

    @classmethod
    async def create(cls, kernel: Kernel, name: str = "WriterAgent"):
        """Async factory method to create WriterAgent with loaded instructions."""
        instruction = await load_prompt("writer_agent", KernelArguments(now=datetime.now()))
        if not instruction:
            raise ValueError("Failed to load writer agent instructions.")

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

        if self.arguments:
            self.arguments.update(now=datetime.now())
        else:
            self.arguments = KernelArguments(now=datetime.now())
        new_instruction = await load_prompt("writer_agent", self.arguments)
        self.instructions = new_instruction if new_instruction else self.instructions

        user_input = None
        if isinstance(messages, str):
            user_input = messages
        elif isinstance(messages, list) and messages:
            user_input = messages[-1].content if isinstance(messages[-1], ChatMessageContent) else messages[-1]
        elif isinstance(messages, ChatMessageContent):
            user_input = messages.content
        else:
            user_input = ""

        async for item in super().invoke_stream(
            messages=[ChatMessageContent(role=AuthorRole.USER, content=user_input)],
            thread=thread,
            on_intermediate_message=on_intermediate_message,
            kernel=self.kernel,
        ):
            yield item

    async def process(self, prompt: str, thread: AgentThread | None, **kwargs) -> Any:
        """Process resume and job description to generate match report."""
        if self.arguments:
            self.arguments.update(now=datetime.now())
        else:
            self.arguments = KernelArguments(now=datetime.now())
        new_instruction = await load_prompt("writer_agent", self.arguments)
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
