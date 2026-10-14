"""Hatch build hook: bundle the official D2 binary into the specworks wheel.

Every wheel build (``uv tool install``, ``uv sync``, ``uv build``) downloads the
pinned D2 release for the target platform, checks its SHA-256 against
``src/specworks/d2_release.json``, and ships it as ``specworks/bin/d2`` (``d2.exe``
on Windows). The wheel is then tagged for that platform.

Environment:
- ``SPECWORKS_D2_BUNDLE=0``: build without D2 (pure wheel; d2 is then looked up on PATH).
- ``SPECWORKS_D2_PLATFORM=<linux|macos|windows>-<amd64|arm64>``: build for another
  platform (used to publish one wheel per platform).
- ``SPECWORKS_D2_CACHE``: where downloaded archives are kept (default: the user cache folder).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import sysconfig
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

ROOT = Path(__file__).parent
RELEASE_FILE = ROOT / "src" / "specworks" / "d2_release.json"
EDITABLE_BIN = ROOT / "src" / "specworks" / "bin"

# Wheel platform tags for cross-builds (static Go binaries, so the oldest common baselines).
WHEEL_TAGS = {
    "linux-amd64": "manylinux2014_x86_64",
    "linux-arm64": "manylinux2014_aarch64",
    "macos-amd64": "macosx_10_12_x86_64",
    "macos-arm64": "macosx_11_0_arm64",
    "windows-amd64": "win_amd64",
    "windows-arm64": "win_arm64",
}


def host_platform() -> str:
    system = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}.get(platform.system())
    machine = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
    if system is None or machine is None:
        raise RuntimeError(
            f"no D2 build for {platform.system()} {platform.machine()}; "
            "set SPECWORKS_D2_BUNDLE=0 to build without it and install d2 yourself"
        )
    return f"{system}-{machine}"


def cache_dir() -> Path:
    if os.environ.get("SPECWORKS_D2_CACHE"):
        return Path(os.environ["SPECWORKS_D2_CACHE"])
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "specworks" / "d2"


def fetch_archive(release: dict, target: str) -> bytes:
    """The release archive for ``target``, from the cache or GitHub, verified against the pinned hash."""
    expected = release["sha256"].get(target)
    if expected is None:
        raise RuntimeError(f"no pinned D2 build for platform '{target}' (known: {', '.join(release['sha256'])})")
    name = f"d2-{release['version']}-{target}.tar.gz"
    cached = cache_dir() / name
    if cached.is_file() and hashlib.sha256(cached.read_bytes()).hexdigest() == expected:
        return cached.read_bytes()

    url = release["url"].format(version=release["version"], platform=target)
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
    except OSError as exc:
        raise RuntimeError(
            f"could not download D2 from {url}: {exc}. "
            "Check the network, or set SPECWORKS_D2_BUNDLE=0 to build without D2 and install d2 yourself."
        ) from exc
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"D2 archive {name} has SHA-256 {actual}, expected {expected}; refusing to bundle it")
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(data)
    except OSError:
        pass  # the cache is only an optimisation
    return data


def extract_binary(archive: bytes, target: str, dest: Path) -> Path:
    exe = "d2.exe" if target.startswith("windows") else "d2"
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        member = next(
            (m for m in tar.getmembers() if m.isfile() and m.name.endswith(f"/bin/{exe}") and "/._" not in m.name),
            None,
        )
        if member is None:
            raise RuntimeError(f"bin/{exe} not found in the D2 archive")
        source = tar.extractfile(member)
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / exe
        with open(path, "wb") as out:
            shutil.copyfileobj(source, out)
    path.chmod(0o755)
    return path


class D2BundleHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        if self.target_name != "wheel" or os.environ.get("SPECWORKS_D2_BUNDLE", "1") == "0":
            return
        release = json.loads(RELEASE_FILE.read_text(encoding="utf-8"))
        cross = os.environ.get("SPECWORKS_D2_PLATFORM")
        target = cross or host_platform()
        archive = fetch_archive(release, target)

        if version == "editable":
            # Editable installs import from src/, so place the binary there (git-ignored).
            extract_binary(archive, target, EDITABLE_BIN)
            return

        staging = Path(tempfile.mkdtemp(prefix="specworks-d2-"))
        binary = extract_binary(archive, target, staging)
        build_data["force_include"][str(binary)] = f"specworks/bin/{binary.name}"
        build_data["pure_python"] = False
        plat = WHEEL_TAGS[target] if cross else sysconfig.get_platform().replace("-", "_").replace(".", "_")
        build_data["tag"] = f"py3-none-{plat}"
