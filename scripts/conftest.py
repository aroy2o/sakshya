"""Makes scripts/*.py importable from scripts/tests/ without packaging."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
