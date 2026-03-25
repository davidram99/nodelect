from nodelect.config import BASE_DIR, NODE_DIST_URL
import urllib.request
import time
import json

VERSIONS_FILE = BASE_DIR / "index.json"

def _download_versions_list() -> None:
    """
    Descarga la lista de versiones disponibles de Node.js desde el sitio oficial.
    Guarda esta lista en un archivo local para futuras consultas.
    """
    url = f"{NODE_DIST_URL}/index.json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            BASE_DIR.mkdir(parents=True, exist_ok=True)
            with open(VERSIONS_FILE, "wb") as f:
                f.write(data)
    except Exception as e:
        print(f"Error al descargar la lista de versiones: {e}")
        raise

def _check_versions_file() -> None:
    """
    Verifica si el archivo con la lista de versiones existe y es reciente.
    Si no existe o es demasiado antiguo, descarga una nueva versión.
    """
    versions_file = VERSIONS_FILE
    if not versions_file.exists() or (versions_file.stat().st_mtime < time.time() - 86400): 
        _download_versions_list()

def _get_lts_online_version() -> str:
    """
    Obtiene la última versión LTS de Node.js
    """
    _check_versions_file()
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        versions = f.read()

    try:
        versions_data = json.loads(versions)
        for version_info in versions_data:
            if version_info.get("lts"):
                return version_info["version"]
        raise ValueError("No se encontró una versión LTS en la lista.")
    
    except json.JSONDecodeError as e:
        print(f"Error al analizar la lista de versiones: {e}")
        raise

def _get_latest_online_version() -> str:
    """
    Obtiene la última versión estable de Node.js
    """
    _check_versions_file()
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        versions = f.read()

    try:
        versions_data = json.loads(versions)
        if versions_data:
            return versions_data[0]["version"]
        else:
            raise ValueError("La lista de versiones está vacía.")
    
    except json.JSONDecodeError as e:
        print(f"Error al analizar la lista de versiones: {e}")
        raise

def _get_uncomplete_version(version: str) -> str:
    """
    Busca la versión más alta que coincida con el prefijo dado
    """
    _check_versions_file()
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        versions = f.read()

    try:
        versions_data = json.loads(versions)
        for version_info in versions_data:
            if version_info["version"].startswith("v" + version):
                return version_info["version"]
        raise ValueError(f"No se encontró una versión que coincida con '{version}'.")
    
    except json.JSONDecodeError as e:
        print(f"Error al analizar la lista de versiones: {e}")
        raise

def parse_version(version: str) -> str:
    """
    Parsea la versión de Node.js, asegurándose de que tenga el formato correcto.
    Si la versión no tiene el prefijo 'v', se lo agrega automáticamente.
    """
    version = version.strip()

    if version.lower() == "lts":
        return _get_lts_online_version()
    elif version.lower() == "latest":
        return _get_latest_online_version()
    elif len(version.split(".")) != 3:
        return _get_uncomplete_version(version)
    
    if not version.startswith("v"):
        version = "v" + version
    
    return version