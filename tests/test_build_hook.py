"""The build hook that bundles D2 (hatch_build.py at the repository root)."""

import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("hatch_build", ROOT / "hatch_build.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def make_archive(name="d2"):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, data in [(f"d2-v0/bin/._{name}", b"apple junk"), (f"d2-v0/bin/{name}", b"#!binary"), ("d2-v0/README.md", b"x")]:
            info = tarfile.TarInfo(path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@pytest.fixture
def release(monkeypatch, tmp_path):
    archive = make_archive()
    monkeypatch.setenv("SPECWORKS_D2_CACHE", str(tmp_path / "cache"))
    data = {"version": "v9.9.9", "url": "https://example.invalid/{version}/{platform}.tar.gz", "sha256": {"linux-amd64": hashlib.sha256(archive).hexdigest()}}
    return data, archive


def test_pinned_release_covers_every_supported_platform():
    pinned = json.loads((ROOT / "src/specworks/d2_release.json").read_text())
    assert set(pinned["sha256"]) == set(hook.WHEEL_TAGS)
    assert all(len(h) == 64 for h in pinned["sha256"].values())


def test_download_is_verified_and_cached(release, monkeypatch):
    data, archive = release
    calls = []

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(hook.urllib.request, "urlopen", lambda url, timeout: calls.append(url) or Response(archive))
    assert hook.fetch_archive(data, "linux-amd64") == archive
    assert calls == ["https://example.invalid/v9.9.9/linux-amd64.tar.gz"]
    assert hook.fetch_archive(data, "linux-amd64") == archive  # second time from the cache
    assert len(calls) == 1


def test_tampered_download_is_refused(release, monkeypatch):
    data, _ = release

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(hook.urllib.request, "urlopen", lambda url, timeout: Response(b"evil"))
    with pytest.raises(RuntimeError, match="refusing to bundle it"):
        hook.fetch_archive(data, "linux-amd64")


def test_download_failure_explains_the_way_out(release, monkeypatch):
    data, _ = release

    def offline(url, timeout):
        raise OSError("network is unreachable")

    monkeypatch.setattr(hook.urllib.request, "urlopen", offline)
    with pytest.raises(RuntimeError, match="SPECWORKS_D2_BUNDLE=0"):
        hook.fetch_archive(data, "linux-amd64")


def test_unknown_platform(release):
    with pytest.raises(RuntimeError, match="no pinned D2 build for platform 'solaris-sparc'"):
        hook.fetch_archive(release[0], "solaris-sparc")


@pytest.mark.parametrize("target, exe", [("linux-amd64", "d2"), ("windows-amd64", "d2.exe")])
def test_extract_skips_apple_metadata(tmp_path, target, exe):
    path = hook.extract_binary(make_archive(exe), target, tmp_path)
    assert path == tmp_path / exe and path.read_bytes() == b"#!binary"


@pytest.mark.parametrize(
    "system, machine, expected",
    [("Linux", "x86_64", "linux-amd64"), ("Linux", "aarch64", "linux-arm64"), ("Darwin", "arm64", "macos-arm64"), ("Windows", "AMD64", "windows-amd64")],
)
def test_host_platform(monkeypatch, system, machine, expected):
    monkeypatch.setattr(hook.platform, "system", lambda: system)
    monkeypatch.setattr(hook.platform, "machine", lambda: machine)
    assert hook.host_platform() == expected


def test_unsupported_host_suggests_building_without_d2(monkeypatch):
    monkeypatch.setattr(hook.platform, "system", lambda: "SunOS")
    with pytest.raises(RuntimeError, match="SPECWORKS_D2_BUNDLE=0"):
        hook.host_platform()
