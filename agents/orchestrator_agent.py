from semantic_kernel.agents import ChatCompletionAgent, GroupChatManager, StringResult, BooleanResult, MessageResult
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from pydantic import ConfigDict
from typing import Any
from .recruiter_agent import RecruiterAgent
from .writer_agent import WriterAgent
from constants import ServiceIDs
from kernel import get_kernel
from utils import load_prompt
import os
import re

class OrchestratorAgent(ChatCompletionAgent, GroupChatManager):
    """Smart router that selects agents based on user input keywords."""
    model_config = ConfigDict(extra="allow")

    current_round: int = 0
    recruiter_agent: RecruiterAgent | None = None
    writer_agent: WriterAgent | None = None

    def __init__(self, kernel, name: str = "OrchestratorAgent", instructions: str = ""):
        ChatCompletionAgent.__init__(
            self,
            kernel=kernel,
            name=name,
            instructions=instructions
        )
        # Initialize GroupChatManager
        GroupChatManager.__init__(self)

        self.max_rounds = 3

        # Initialize Azure OpenAI service for orchestration processing
        if not self.kernel.services.get(ServiceIDs.AZURE_ORCHESTRATOR_SERVICE):
            az_orchestrator_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_ORCHESTRATOR_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            self.kernel.add_service(az_orchestrator_service)

    @classmethod
    async def create(cls, name: str = "OrchestratorAgent"):
        """Async factory method to create OrchestratorAgent."""
        kernel, _ = get_kernel()
        recruiter_agent = await RecruiterAgent.create()
        writer_agent = await WriterAgent.create()

        instructions = await load_prompt("orchestrator_agent", KernelArguments(
            recruiter_name=recruiter_agent.name,
            recruiter_service_id=ServiceIDs.AZURE_HR_SERVICE,
            recruiter_instructions=recruiter_agent.instructions,
            writer_name=writer_agent.name,
            writer_service_id=ServiceIDs.AZURE_WRITER_SERVICE,
            writer_instructions=writer_agent.instructions,
        ))

        instance = cls(kernel=kernel, name=name)
        # Attach variables to the instance after initialization
        if instructions:
            instance.instructions = instructions
        instance.recruiter_agent = recruiter_agent
        instance.writer_agent = writer_agent
        return instance

    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        return BooleanResult(result=False, reason="OrchestratorAgent does not require user input for routing decisions.")

    async def select_next_agent(self, chat_history: ChatHistory, participant_descriptions: dict[str, str]) -> StringResult:
        last_messages = chat_history.messages[-4:]
        selected = await self.detect_intent(ChatHistory(last_messages))

        return StringResult(result=str(selected), reason=f"{selected} selected based on user intent.")

    async def filter_results(
        self,
        chat_history: ChatHistory,
    ) -> MessageResult:
        """Filter the results of the group chat.

        Args:
            chat_history (ChatHistory): The chat history of the group chat.
            participant_descriptions (dict[str, str]): The descriptions of the participants in the group chat.
        """
        return MessageResult(
            result=ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content="Orchestrator will handle the response."
            ), reason="OrchestratorAgent does not filter results.")

    async def detect_intent(self, chat_history: ChatHistory):
        """Detect the intent of the user's message and route to the appropriate agent."""
        last_messages = chat_history.messages[-4:] if len(chat_history.messages) > 4 else chat_history.messages
        messages = []
        for message in last_messages:
            if isinstance(message, (str, ChatMessageContent)):
                messages.append(message)
        history_str = "\n".join(
            f"{msg.role.value}: {msg.content}" if isinstance(msg, ChatMessageContent) else str(msg)
            for msg in messages
        )
        instruction = f"{self.instructions}\n\nChat History:\n{history_str}\n\nUser Input: {messages[-1].content if messages else ''}"
        if instruction:
            self.instructions = instruction
        intent = await self.get_response(messages=messages)
        return intent

    async def process(self, chat_history: ChatHistory, **kwargs) -> dict[str, Any]:
        """Process the chat history and route to the appropriate agent."""
        user_input = kwargs.get("user_input", "")
        resume_file = kwargs.get("resume_file", None)
        jd = kwargs.get("jd", None)
        if not user_input:
            return {
                "result": "No user input provided.",
                "reason": "User input is required to process the request."
            }
        if not chat_history or not chat_history.messages:
            chat_history = ChatHistory()
            chat_history.add_message(
                ChatMessageContent(role=AuthorRole.USER, content=user_input)
            )
        intent = await self.detect_intent(chat_history)
        # Retrieve service_id from intent string e.g. service_id=az_hr_service
        match = re.search(r'service_id=([a-zA-Z0-9_]+)', str(intent))
        if match:
            service_id = match.group(1)
            print(f"routing to service_id: {service_id}")
        return {
            "result": intent,
            "reason": "",
            "chat_history": chat_history,
        }