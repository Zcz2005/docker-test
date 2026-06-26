from __future__ import annotations

import argparse

from southnotary_uploader.env_loader import load_dotenv_if_available

from .config import ScrcpyManagerConfig
from .logging_setup import cleanup_old_files, setup_root_logging
from .runtime import RuntimeController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Android scrcpy forensic recording manager")
    parser.add_argument("--config", help="Path to config.ini")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_available()
    args = build_parser().parse_args(argv)
    config = ScrcpyManagerConfig.load(args.config)
    config.ensure_directories()

    setup_root_logging(config.paths.logs)
    cleanup_old_files(config.paths.logs, days_to_keep=config.system.log_retention_days, label="日志")

    RuntimeController(config).run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
