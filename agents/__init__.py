from abc import ABC, abstractmethod
from semantic_kernel.agents import Agent, ChatHistoryAgentThread


class BaseAgent(Agent, ABC):
    """Abstract base class for SK agents."""

    @abstractmethod
    async def process(self, prompt: str, **kwargs) -> dict | str:
        """Process the input data and return the result."""
        pass