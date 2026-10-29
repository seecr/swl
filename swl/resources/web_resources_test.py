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
