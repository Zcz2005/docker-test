"""Legacy entrypoint kept for operators migrating from the monolithic script.

The original single-file implementation has been refactored into the
`southnotary_uploader` package. This script preserves a familiar startup path:

    python legacy/oos_uploader_southnotary.py

Configure credentials via environment variables or a `.env` file in the project root.
"""

from southnotary_uploader.cli import main
from southnotary_uploader.env_loader import load_dotenv_if_available


if __name__ == "__main__":
    load_dotenv_if_available()
    raise SystemExit(main())
