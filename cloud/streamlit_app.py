"""Streamlit Community Cloud entrypoint for the resource-bounded free demo."""

import os
import runpy
from pathlib import Path


os.environ["NOTEBOT_PROFILE"] = "cloud"
APP_PATH = Path(__file__).resolve().parents[1] / "asfi_notebot.py"
runpy.run_path(str(APP_PATH), run_name="__main__")
