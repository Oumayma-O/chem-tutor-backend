"""Run admin bootstrap once (same as app startup). Use after `scripts.seed --clean`."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.connection import AsyncSessionFactory
from app.services.auth.bootstrap import ensure_admin_user


async def main() -> None:
    async with AsyncSessionFactory() as session:
        await ensure_admin_user(session)


if __name__ == "__main__":
    asyncio.run(main())
