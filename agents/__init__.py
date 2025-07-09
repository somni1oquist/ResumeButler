from typing import Any
from abc import ABC, abstractmethod
from user_profile import UserProfile
from semantic_kernel.agents import Agent, AgentThread


class BaseAgent(Agent, ABC):
    """Abstract base class for SK agents."""
    _context: UserProfile = UserProfile()
    _thread: AgentThread | None = None

    @classmethod
    @abstractmethod
    async def create(cls, name: str = "BaseAgent") -> 'BaseAgent':
        """Async factory method to create an instance of the agent with loaded instructions."""
        pass

    @abstractmethod
    async def process(self, prompt: str, thread: AgentThread | None, **kwargs) -> Any:
        """Process the prompt and return a response or tool output."""
        pass

    