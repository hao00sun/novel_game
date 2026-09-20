from __future__ import annotations

import argparse

from .app.bootstrap import ENV_PATH
from .app.cli import main
from .infrastructure.config import configure_provider


def entrypoint():
    parser = argparse.ArgumentParser(description="Novel World")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="在终端配置 mock 或 OpenAI-compatible API Provider。",
    )
    args = parser.parse_args()
    if args.configure:
        configure_provider(ENV_PATH)
        return
    main()


if __name__ == "__main__":
    entrypoint()
