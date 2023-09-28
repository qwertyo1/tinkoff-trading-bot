import asyncio
import logging

from app.client import client
from app.instruments_config.parser import instruments_config
from app.settings import settings
from app.strategies.strategy_fabric import resolve_strategy

logging.basicConfig(
    level=settings.log_level,
    format="[%(levelname)-5s] %(asctime)-19s %(name)s:%(lineno)d: %(message)s",
)
logging.getLogger("tinkoff").setLevel(settings.tinkoff_library_log_level)


async def run():
    await client.ainit()
    spawned_tasks = []
    for instrument_config in instruments_config.instruments:
        strategy = resolve_strategy(
            strategy_name=instrument_config.strategy.name,
            figi=instrument_config.figi,
            **instrument_config.strategy.parameters
        )
        spawned_tasks.append(asyncio.create_task(strategy.start()))
    await asyncio.wait(spawned_tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(run()))
