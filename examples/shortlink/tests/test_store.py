import re

import pytest

from shortlink.errors import ExpiredCode, InvalidUrl, UnknownCode
from shortlink.store import LinkStore


# @ac AC-LINK-001.1
def test_ac_link_001_1_valid_url_gets_a_code():
    code = LinkStore().shorten("https://example.com/a")
    assert re.fullmatch(r"[A-Za-z0-9]{6}", code)


# @ac AC-LINK-001.2
def test_ac_link_001_2_same_url_keeps_its_code():
    store = LinkStore()
    assert store.shorten("https://example.com/a") == store.shorten("https://example.com/a")


# @ac AC-LINK-001.3
@pytest.mark.parametrize("url", ["ftp://example.com", "not a url", "https://", "http:///path"])
def test_ac_link_001_3_non_http_url_is_rejected(url):
    with pytest.raises(InvalidUrl):
        LinkStore().shorten(url)


# @ac AC-LINK-002.1
def test_ac_link_002_1_known_code_resolves():
    store = LinkStore()
    code = store.shorten("https://example.com/a")
    assert store.resolve(code) == "https://example.com/a"


# @ac AC-LINK-002.2
def test_ac_link_002_2_unknown_code_is_rejected():
    with pytest.raises(UnknownCode):
        LinkStore().resolve("zzzzzz")


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


# @ac AC-LINK-003.1
def test_ac_link_003_1_code_resolves_before_its_lifetime_ends():
    clock = FakeClock()
    store = LinkStore(clock=clock)
    code = store.shorten("https://example.com/a", ttl=60)
    clock.now = 59
    assert store.resolve(code) == "https://example.com/a"


# @ac AC-LINK-003.2
def test_ac_link_003_2_non_positive_lifetime_is_rejected():
    with pytest.raises(ValueError):
        LinkStore().shorten("https://example.com/a", ttl=0)


# @ac AC-LINK-002.3
def test_ac_link_002_3_expired_code_is_rejected():
    clock = FakeClock()
    store = LinkStore(clock=clock)
    code = store.shorten("https://example.com/a", ttl=60)
    clock.now = 60
    with pytest.raises(ExpiredCode):
        store.resolve(code)
