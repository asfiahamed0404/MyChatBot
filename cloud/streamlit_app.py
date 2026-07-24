"""Streamlit Community Cloud entrypoint for the resource-bounded free demo."""

import os
import runpy
import sys
from pathlib import Path


os.environ["NOTEBOT_PROFILE"] = "cloud"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_PATH = PROJECT_ROOT / "asfi_notebot.py"
runpy.run_path(str(APP_PATH), run_name="__main__")
