from semantic_kernel.agents import GroupChatManager, StringResult, BooleanResult, AgentThread, MessageResult
from semantic_kernel.contents import ChatHistory
from recruiter_agent import RecruiterAgent
from writer_agent import WriterAgent
from kernel import get_kernel

class OrchestratorAgent(GroupChatManager):
    """Smart router that selects agents based on user input keywords."""

    recruiter_agent: RecruiterAgent
    writer_agent: WriterAgent
    thread: AgentThread | None

    def __init__(self, kernel):
        self.kernel = kernel

    @classmethod
    async def create(cls, name: str = "OrchestratorAgent"):
        """Async factory method to create OrchestratorAgent."""
        kernel, _ = get_kernel()
        cls.recruiter_agent = await RecruiterAgent.create()
        cls.writer_agent = await WriterAgent.create()
        return cls(kernel=kernel)

    @staticmethod
    def detect_intent(message: str) -> str:
        message = message.lower()
        if any(keyword in message for keyword in ["revise", "rewrite", "reword", "improve"]):
            return "WriterAgent"
        elif any(keyword in message for keyword in ["review", "analyze", "match", "assess"]):
            return "RecruiterAgent"
        return "RecruiterAgent"

    async def should_request_user_input(self, thread) -> BooleanResult:
        return BooleanResult(result=False)

    async def select_next_agent(self, chat_history: ChatHistory, participant_descriptions: dict[str, str]) -> StringResult:
        last_message = chat_history.messages[-1].content
        selected = self.detect_intent(last_message)
        return StringResult(result=selected, reason=f"I selected {selected} based on the user's last message.")

    async def filter_results(
        self,
        chat_history: ChatHistory,
    ) -> MessageResult:
        """Filter the results of the group chat.

        Args:
            chat_history (ChatHistory): The chat history of the group chat.
            participant_descriptions (dict[str, str]): The descriptions of the participants in the group chat.
        """
        pass