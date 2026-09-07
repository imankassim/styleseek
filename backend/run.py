"""Local dev entrypoint. On Windows, asyncio defaults to ProactorEventLoop, which psycopg's
async mode doesn't support — this sets the Selector policy before uvicorn starts. Not needed on
Linux/macOS, where this is a no-op deployment target (Stage 15 containers will run on Linux).
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
