from nodelect.config import VERSIONS_DIR, NODE_DIST_URL

import urllib.request
import sys
import threading
import itertools
import time
from pathlib import Path
import hashlib
import zipfile
import shutil
import tempfile 
import os

class ChecksumVerificationError(Exception):
    pass

def _get_download_url(version: str) -> str:
    return f"{NODE_DIST_URL}/{version}/node-{version}-win-x64.zip"

def _get_checksum_url(version: str) -> str:
    return f"{NODE_DIST_URL}/{version}/SHASUMS256.txt"

def _progress_bar(downloaded: int, total: int) -> None:
    if total <= 0:
        return
    percent = min(downloaded / total, 1.0)
    filled = int(40 * percent)
    bar = "█" * filled + "░" * (40 - filled)
    mb_down = downloaded / 1_048_576
    mb_total = total / 1_048_576
    sys.stdout.write(f"\rDownloading... [{bar}] {percent:.0%} ({mb_down:.1f}/{mb_total:.1f} MB)")
    sys.stdout.flush()
    if percent == 1.0:
        sys.stdout.write("\n")

def _spinner(message: str, stop_event: threading.Event) -> None:
    for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r{message} {frame}")
        sys.stdout.flush()
        time.sleep(0.08)

def _download_node_version(url: str, target: Path) -> None:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            total_size = int(response.getheader("Content-Length", 0))
            block_size = 65536
            downloaded = 0

            with open(target, "wb") as out_file:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    out_file.write(buffer)
                    downloaded += len(buffer)
                    _progress_bar(downloaded, total_size)
    except Exception as e:
        if target.exists():
            target.unlink()
        raise ValueError(f"Failed to download Node.js from {url}: {e}")

def _fetch_expected_checksum(version: str, filename: str) -> str:
    url = _get_checksum_url(version)
    with urllib.request.urlopen(url, timeout=30) as response:
        for line in response:
            decoded = line.decode("utf-8").strip()
            if decoded.endswith(filename):
                return decoded.split()[0]
    raise ValueError(f"Checksum for {filename} not found")

def _verify_checksum(file_path: Path, expected: str) -> None:
    sha256 = hashlib.sha256()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=_spinner, args=("Verifying integrity...", stop_event), daemon=True)
    spinner_thread.start()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        if sha256.hexdigest() != expected:
            raise ChecksumVerificationError(f"Integrity verification failed ❌")
        sys.stdout.write("\rIntegrity verification passed ✔️\n")

    finally:
        stop_event.set()
        spinner_thread.join()

def _extract_zip(zip_path: Path, version: str) -> Path:
    extract_dir = (VERSIONS_DIR / version).resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        total = len(members)

        for i, member in enumerate(members, 1):
            parts = Path(member).parts
            if len(parts) > 1:
                relative = Path(*parts[1:])
                target = (extract_dir / relative).resolve()
                if not target.is_relative_to(extract_dir):
                    raise ValueError(f"Unsafe path detected in zip: {member}")
                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, "wb") as out:
                        shutil.copyfileobj(src, out)

            percent = i / total
            filled = int(40 * percent)
            bar = "█" * filled + "░" * (40 - filled)
            sys.stdout.write(f"\rExtracting... [{bar}] {percent:.0%} ({i}/{total})")
            sys.stdout.flush()

    sys.stdout.write("\n")
    print(f"Node.js {version} installed successfully ✔️")
    return extract_dir

def install_node_version(version: str) -> None:
    filename = f"node-{version}-win-x64.zip"
    url = _get_download_url(version)

    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    tmp_dir, tmp_path = tempfile.mkstemp(dir=VERSIONS_DIR, prefix=f"node-{version}-", suffix=".zip")
    zip_path = Path(tmp_path)
    os.close(tmp_dir)

    try:
        # Download the files from the official Node.js distribution site
        _download_node_version(url, zip_path)

        # Verify the integrity of the downloaded file using the official checksums
        expected_checksum = _fetch_expected_checksum(version, filename)
        _verify_checksum(zip_path, expected_checksum)
        
        # Extract the downloaded zip file to the versions directory
        _extract_zip(zip_path, version)

    except ChecksumVerificationError as e:
        sys.stdout.write("\r" + " " * 50 + "\r")
        print(f"Error: {e}")

    finally:
        if zip_path.exists():
            zip_path.unlink()