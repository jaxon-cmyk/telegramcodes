"""Background worker entrypoint.

Production should run this as a separate process on Oracle. The worker owns:
- Telegram history sync and real-time listener loops.
- Signal parsing from newly stored messages.
- Automation rule evaluation and trade-intent queueing.
- MT5 bridge health checks and provider failure audit logs.
"""

import asyncio


async def main() -> None:
    while True:
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
