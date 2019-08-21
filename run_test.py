import asyncio

loop = asyncio.get_event_loop()

from test.user_test import test_cases, init
from set_logging import set_logger
async def main():
    set_logger()
    await init()
    for item in test_cases:
        await item()

loop.run_until_complete(main())
