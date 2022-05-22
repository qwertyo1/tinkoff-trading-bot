from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    @abstractmethod
    def __init__(self, figi: str, *args, **kwargs):
        pass

    @abstractmethod
    async def start(self):
        pass
