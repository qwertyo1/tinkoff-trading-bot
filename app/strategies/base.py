from abc import ABC, abstractmethod

from tinkoff.invest import AsyncClient
from tinkoff.invest.async_services import AsyncServices


class BaseStrategy(ABC):
    @abstractmethod
    def __init__(self, client: AsyncServices, figi: str, *args, **kwargs):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
