"""Import this module first in any test that resolves local settings.

It points ``PT_RESEARCH_HOME`` at a fresh, empty temporary directory and clears
``PT_LOCAL_REFERENCES_DIR``, so a test run can never read (or write) the developer's real
``~/.config/pt-research``. The directory is removed when the interpreter exits.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

_BASE = Path(tempfile.mkdtemp(prefix="pt-test-home-"))
ISOLATED_HOME = _BASE / "pt-research"
os.environ["PT_RESEARCH_HOME"] = str(ISOLATED_HOME)
os.environ.pop("PT_LOCAL_REFERENCES_DIR", None)
atexit.register(shutil.rmtree, _BASE, True)
