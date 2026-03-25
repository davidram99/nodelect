from nodelect.config import VERSIONS_DIR, CURRENT_FILE

def list_versions() -> None:
    if not VERSIONS_DIR.exists():
        print("No Node.js versions installed.")
        return
    versions = [d.name for d in VERSIONS_DIR.iterdir() if d.is_dir()]
    if not versions:
        print("No Node.js versions installed.")
        return
    current_version = None
    if CURRENT_FILE.exists():
        current_version = CURRENT_FILE.read_text().strip()
    for v in sorted(versions):
        marker = " (current)" if v == current_version else ""
        print(f"- {v}{marker}")