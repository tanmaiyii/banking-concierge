"""Quick smoke-test entry point.

For the full chat experience, run:

    uv run langgraph dev

and open Studio at http://localhost:2024.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv(override=True)

from concierge.graph import graph  # noqa: E402


def main() -> None:
    question = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "What is the monthly fee on Everyday Checking?"
    )
    # Populate root-run metadata so the Threads view can group multi-turn
    # sessions, per-rep filtering works, and prod/staging traces stay separate.
    config = {
        "metadata": {
            "thread_id": os.environ.get("CONCIERGE_THREAD_ID", str(uuid.uuid4())),
            "user_id": os.environ.get("CONCIERGE_USER_ID", "smoke-test"),
            "environment": os.environ.get("APP_ENV", "development"),
        },
        "run_name": "agent",
    }
    result = graph.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
