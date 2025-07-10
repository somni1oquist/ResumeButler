from semantic_kernel.agents import Agent, ChatCompletionAgent, AgentThread, GroupChatManager, StringResult, BooleanResult, MessageResult
from semantic_kernel.contents import ChatHistory, AuthorRole
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from pydantic import ConfigDict
from typing import Any
from plugins import RecruiterPlugin, RevisionPlugin
from .recruiter_agent import RecruiterAgent
from .writer_agent import WriterAgent
from constants import ServiceIDs
from kernel import get_kernel
from user_profile import UserProfile
from utils import load_prompt, get_parser_manager
import os

class OrchestratorAgent(ChatCompletionAgent, GroupChatManager):
    """Smart router that selects agents based on user input keywords."""
    model_config = ConfigDict(extra="allow")
    max_rounds: int | None = 5
    current_round: int = 0
    # @TODO: Gather agents dynamically based on the task
    recruiter_agent: RecruiterAgent | None = None
    writer_agent: WriterAgent | None = None
    _context: dict[str, Any] = {}
    _thread: AgentThread | None = None

    def __init__(self, name: str = "OrchestratorAgent", instructions: str = ""):
        kernel, _ = get_kernel()
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
        if not kernel.services.get(ServiceIDs.AZURE_ORCHESTRATOR_SERVICE):
            az_orchestrator_service = AzureChatCompletion(
                service_id=ServiceIDs.AZURE_ORCHESTRATOR_SERVICE,
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
            kernel.add_service(az_orchestrator_service)

    @classmethod
    async def create(cls, name: str = "OrchestratorAgent"):
        """Async factory method to create OrchestratorAgent."""
        kernel, _ = get_kernel()
        # Register recruiter and writer agents to the kernel
        recruiter_agent = await RecruiterAgent.create(kernel=kernel)
        writer_agent = await WriterAgent.create(kernel=kernel)

        instructions = await load_prompt("orchestrator_agent", KernelArguments(
            recruiter_name=recruiter_agent.name,
            recruiter_service_id=ServiceIDs.AZURE_HR_SERVICE,
            recruiter_instructions=recruiter_agent.instructions,
            writer_name=writer_agent.name,
            writer_service_id=ServiceIDs.AZURE_WRITER_SERVICE,
            writer_instructions=writer_agent.instructions,
        ))

        instance = cls(name=name)
        # Attach variables to the instance after initialization
        if instructions:
            instance.instructions = instructions
        instance.recruiter_agent = recruiter_agent
        instance.writer_agent = writer_agent
        kernel.add_plugin(RecruiterPlugin(), plugin_name="RecruiterPlugin")
        kernel.add_plugin(RevisionPlugin(), plugin_name="RevisionPlugin")
        # Ensure the same kernel is set for the instance
        instance.kernel = kernel
        return instance

    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        last_msg = chat_history.messages[-1]
        # @TODO: Implement logic to determine if user input is needed
        if last_msg.role == AuthorRole.ASSISTANT:
            return BooleanResult(result=True, reason="Waiting for user input after agent response.")
        return BooleanResult(result=False, reason="Still processing or waiting for agent.")

    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Determine if the conversation should be terminated."""
        print("Checking if conversation should terminate...")
        return BooleanResult(
            result=False,
            reason="Testing termination logic, always returning False."
        )

    async def select_next_agent(self, chat_history: ChatHistory, participant_descriptions: dict[str, str]) -> StringResult:
        should_terminate = await self.should_terminate(chat_history=chat_history)
        if should_terminate.result:
            return StringResult(result="terminate", reason="Max rounds or task complete.")

        # Detect intent
        next_service = await self.detect_intent(chat_history)
        if next_service == "terminate":
            return StringResult(result="terminate", reason="Intent detection says we're done.")

        return StringResult(result=next_service, reason=f"{next_service} selected based on intent.")

    async def filter_results(
        self,
        chat_history: ChatHistory,
    ) -> MessageResult:
        """Filter results to return the last assistant or tool output."""
        for msg in reversed(chat_history.messages):
            if msg.role in (AuthorRole.ASSISTANT, AuthorRole.TOOL):
                return MessageResult(result=msg, reason="Returning last assistant or tool output.")
        return MessageResult(result=chat_history.messages[-1], reason="Default last message used.")

    async def detect_intent(self, chat_history: ChatHistory):
        """Detect the intent of the user's message and route to the appropriate agent."""
        last_messages = chat_history.messages[-4:] if len(chat_history.messages) > 4 else chat_history.messages
        
        history_str = "\n".join(f"{msg.role.value}: {msg.content}" for msg in last_messages if hasattr(msg, "content"))
        prompt = (
            f"{self.instructions}\n\n"
            f"Conversation:\n{history_str}"
        )

        intent = await self.kernel.invoke_prompt(prompt=prompt)
        intent_str = str(intent).strip().lower()

        if ServiceIDs.AZURE_HR_SERVICE in intent_str and self.recruiter_agent:
            return self.recruiter_agent.name
        elif ServiceIDs.AZURE_WRITER_SERVICE in intent_str and self.writer_agent:
            return self.writer_agent.name
        elif "terminate" in intent_str or "end" in intent_str:
            return "terminate"
        else:
            # Fallback to default agent
            return self.recruiter_agent.name if self.recruiter_agent else "terminate"
        
    def get_agents(self) -> list[Agent]:
        """Return a list of agents available for routing."""
        agents = []
        if self.recruiter_agent:
            agents.append(self.recruiter_agent)
        if self.writer_agent:
            agents.append(self.writer_agent)
        return agents
    
    def set_context(self, context: dict[str, Any]) -> None:
        """Set the context for the orchestrator agent."""
        _parser = get_parser_manager()
        user_profile = UserProfile(
            resume=_parser.parse_document(context.get("resume_file", b"")),
            jd=context.get("jd", None)
        )
        for agent in self.get_agents():
            agent.arguments = KernelArguments(
                resume=user_profile.resume,
                jd=user_profile.jd,
            )