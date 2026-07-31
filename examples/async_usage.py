import asyncio

from pharos_sdk import AsyncPharosClient


async def with_context_manager() -> None:
    async with AsyncPharosClient("phk_live_...") as client:
        importers = await client.importers.list()
        latest = await client.declarations.latest(limit=10)
        print(importers.count, latest.count)


async def without_context_manager() -> None:
    client = AsyncPharosClient("phk_live_...")
    importers = await client.importers.list()
    latest = await client.declarations.latest(limit=10)
    print(importers.count, latest.count)
    await client.close()


async def main() -> None:
    await with_context_manager()
    await without_context_manager()


asyncio.run(main())
