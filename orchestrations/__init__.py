from abc import ABC, abstractmethod


class Orchestrator(ABC):
    @abstractmethod
    def run(self, input_data: dict) -> dict:
        pass
