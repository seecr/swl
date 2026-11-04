"""python -m pytest site/news_test.py"""

import pytest

from news import news

CHANGELOG = """# Changelog

## Unreleased

> Not yet.

## 5.7.0 (2026-11-05)

> Trees: a tree that the server fills and drives.
> Also: help balloons.

### Added

- Trees

## 5.6.1 (2026-11-04)

### Changed

- A fix

## 5.6.0 (2026-11-03)

### Added

- Help balloons
"""


def test_the_release_and_its_bugfixes():
    expected = {
        "version": "5.7",
        "text": "Trees: a tree that the server fills and drives. Also: help balloons.",
    }
    assert news(CHANGELOG, "5.7.0") == expected
    assert news(CHANGELOG, "5.7.3") == expected
    assert news(CHANGELOG, "5.7.0-4-gabc1234") == expected


def test_no_highlights():
    assert news(CHANGELOG, "5.6.1") == {}  # an older release: no banner
    assert news(CHANGELOG, "main") == {}
    with pytest.raises(SystemExit, match="5.6.0 has no highlights"):
        news(CHANGELOG, "5.6.0")
