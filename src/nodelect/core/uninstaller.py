from nodelect.config import VERSIONS_DIR
import shutil


def uninstall_node_version(version: str) -> None:
    version_dir = VERSIONS_DIR / version
    if version_dir.exists():
        shutil.rmtree(version_dir)
        current_version = (VERSIONS_DIR.parent / "current").read_text().strip()
        if current_version == version:
            (VERSIONS_DIR.parent / "current").write_text("")
        print(f"Versión {version} desinstalada correctamente.")
    else:
        print(f"La versión {version} no está instalada.")