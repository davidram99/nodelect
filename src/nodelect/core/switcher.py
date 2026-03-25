from nodelect.config import VERSIONS_DIR, CURRENT_FILE

def use_version(version: str, lts: bool = False, latest: bool = False) -> None:
    version_dir = VERSIONS_DIR / version
    if not version_dir.exists():
        if lts:
            print(f"Actual LTS version: {version}, is not installed. Please install it first using 'nodelect install {version}'.")
        if latest:
            print(f"Actual latest version: {version}, is not installed. Please install it first using 'nodelect install {version}'.")
        else:
            print(f"Version {version} is not installed. Please install it first using 'nodelect install {version}'.")
        return
    
    CURRENT_FILE.write_text(version)
    print(f"Switched to Node.js version {version} successfully ✔️")