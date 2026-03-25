from pathlib import Path

BASE_DIR = Path.home() / "AppData" / "Local" / "nodelect"
VERSIONS_DIR = BASE_DIR / "nodejs" / "versions"
SHIMS_DIR = BASE_DIR / "nodejs" / "shims"
CURRENT_FILE = BASE_DIR / "nodejs" / "current"
NODE_DIST_URL = "https://nodejs.org/dist"