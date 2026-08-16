"""Phase 11/12 one-command entry point (see src/civitas_evaluation/__main__.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from civitas_evaluation.__main__ import main

if __name__ == "__main__":
    sys.exit(main())