from pharos_sdk import PharosClient


def with_context_manager() -> None:
    with PharosClient("phk_live_...") as client:
        importers = client.importers.list()
        latest = client.declarations.latest(limit=10)
        print(importers.count, latest.count)


def without_context_manager() -> None:
    client = PharosClient("phk_live_...")
    importers = client.importers.list()
    latest = client.declarations.latest(limit=10)
    print(importers.count, latest.count)
    client.close()


with_context_manager()
without_context_manager()
