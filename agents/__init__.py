from abc import ABC, abstractmethod
from semantic_kernel.agents import Agent, ChatHistoryAgentThread


class BaseAgent(Agent, ABC):
    """Abstract base class for SK agents."""

    @classmethod
    @abstractmethod
    async def create(cls, name: str = "BaseAgent") -> 'BaseAgent':
        """Async factory method to create an instance of the agent with loaded instructions."""
        pass

    @abstractmethod
    async def process(self, prompt: str, **kwargs) -> dict | str:
        """Process the input data and return the result."""
        pass

    