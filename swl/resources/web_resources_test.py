## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2025-2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

import json
import re
from pathlib import Path

import pytest

from .web_resources import WebResources


def test_web_resources_default():
    res = WebResources()
    assert len(res.styles) == 2


def test_web_resources_path_as_string(tmp_path):
    tmp_path.joinpath("test.json").write_text(json.dumps({"styles": [{"href": "a.css"}]}))
    assert WebResources(str(tmp_path / "test.json")).styles[0]["href"] == "a.css"


def test_web_resources_custom(tmp_path):
    tmp_path.joinpath("test.json").write_text(
        json.dumps(
            {
                "styles": [{"href": "test.css", "integrity": "sha256-123"}],
                "scripts": [
                    {"src": "test.js"},
                    {"src": "test2.js", "integrity": "sha256-123"},
                ],
            }
        )
    )
    res = WebResources(tmp_path / "test.json")
    assert len(res.styles) == 1
    assert len(res.scripts) == 2
    assert res.styles[0]["href"] == "test.css"
    assert res.scripts[0]["src"] == "test.js"


def test_invalid_data(tmp_path):
    (test_path := tmp_path / "test.json").write_text("invalid json")

    with pytest.raises(ValueError):
        WebResources(test_path)

    test_path.write_text(json.dumps({"styles": "invalid"}))
    with pytest.raises(ValueError):
        WebResources(test_path)


def test_package_and_own(tmp_path):
    (test_path := tmp_path / "test.json").write_text(
        json.dumps(
            {
                "styles": [
                    {"href": "https://cdn.example.org/site.css", "own": True},
                ],
                "scripts": [
                    {"src": "https://cdn.example.org/x.js", "package": "somelib@1.2.3"},
                ],
            }
        )
    )
    res = WebResources(test_path)
    assert res.styles[0]["own"] is True
    assert res.scripts[0]["package"] == "somelib@1.2.3"


def test_unknown_key(tmp_path):
    (test_path := tmp_path / "test.json").write_text(
        json.dumps({"scripts": [{"src": "x.js", "pakage": "somelib@1.2.3"}]})
    )
    with pytest.raises(ValueError, match="Invalid key"):
        WebResources(test_path)


def test_integrity(tmp_path):
    tmp_path.joinpath("test.json").write_text(
        json.dumps(
            {
                "styles": [
                    {"href": "test.css", "integrity": "sha256-123"},
                    {"href": "test2.css"},
                ],
                "scripts": [
                    {"src": "test.js"},
                ],
            }
        )
    )
    res = WebResources(tmp_path / "test.json")
    assert len(res.styles) == 2
    assert res.styles[0]["integrity"] == "sha256-123"
    assert res.styles[1]["integrity"] == ""

    assert len(res.scripts) == 1
    assert res.scripts[0]["integrity"] == ""


def test_extra(tmp_path):
    tmp_path.joinpath("main.json").write_text(
        json.dumps({"styles": [{"href": "main.css"}], "scripts": [{"src": "main.js"}]})
    )
    tmp_path.joinpath("tree.json").write_text(
        json.dumps({"styles": [{"href": "tree.css"}], "scripts": [{"src": "tree.js"}]})
    )
    tmp_path.joinpath("more.json").write_text(json.dumps({"scripts": [{"src": "x.js"}]}))
    res = WebResources(tmp_path / "main.json", extra=tmp_path / "tree.json")
    assert [s["href"] for s in res.styles] == ["main.css", "tree.css"]
    assert [s["src"] for s in res.scripts] == ["main.js", "tree.js"]

    res = WebResources(
        tmp_path / "main.json",
        extra=[str(tmp_path / "tree.json"), tmp_path / "more.json"],
    )
    assert [s["src"] for s in res.scripts] == ["main.js", "tree.js", "x.js"]


def test_extra_after_default(tmp_path):
    tmp_path.joinpath("tree.json").write_text(json.dumps({"scripts": [{"src": "t.js"}]}))
    res = WebResources(extra=[tmp_path / "tree.json"])
    assert len(res.styles) == 2
    assert res.scripts[-1]["src"] == "t.js"


ICONS = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css"


def test_icons_stylesheet_kept_by_default():
    hrefs = [style["href"] for style in WebResources().styles]
    assert ICONS in hrefs


def test_icons_stylesheet_replaced():
    res = WebResources(icons_stylesheet={"href": "/static/phosphor.css"})
    hrefs = [style["href"] for style in res.styles]
    assert ICONS not in hrefs
    assert hrefs[1] == "/static/phosphor.css", "in its place"
    assert res.styles[1]["integrity"] == ""


def test_icons_stylesheet_left_out():
    res = WebResources(icons_stylesheet=False)
    assert [style["href"] for style in res.styles] == [
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
    ]


def test_icons_stylesheet_without_one_in_the_resources(tmp_path):
    path = tmp_path / "own.json"
    path.write_text(json.dumps({"styles": [{"href": "a.css"}]}))
    res = WebResources(path, icons_stylesheet={"href": "icons.css"})
    assert [style["href"] for style in res.styles] == ["a.css", "icons.css"]


def test_icons_stylesheet_invalid():
    with pytest.raises(ValueError, match="Missing href"):
        WebResources(icons_stylesheet={"src": "icons.css"})


RESOURCE_FILES = sorted(Path(__file__).parent.glob("*-web-resources.json")) + [
    Path(__file__).parents[2] / "example" / "swl_tasks" / "tree-web-resources.json"
]
JSDELIVR = re.compile(r"^https://cdn\.jsdelivr\.net/npm/((?:@[^/@]+/)?[^/@]+)@([^/]+)/")


@pytest.mark.parametrize("path", RESOURCE_FILES, ids=lambda path: path.name)
def test_every_entry_names_its_package(path):
    """For tools that check for outdated libraries: every library in SWL's own resource
    files has "package" (name@version, the same as in its url), every file of SWL itself
    "own": true."""
    data = json.loads(path.read_text())
    for entry in data["styles"] + data["scripts"]:
        url = entry.get("href") or entry.get("src")
        if entry.get("own"):
            assert url.startswith("/") and "package" not in entry, url
            continue
        match = JSDELIVR.match(url)
        assert match, url
        assert entry.get("package") == f"{match[1]}@{match[2]}", url
