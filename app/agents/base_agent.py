from abc import ABC, abstractmethod

class BaseAgent(ABC):

    @abstractmethod
    async def run(self, message: str):
        pass