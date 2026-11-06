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

import importlib.resources
import json
import pathlib

# Fields an entry may have besides "href" (styles) or "src" (scripts): "integrity" (the
# SRI hash), and for tools that check for outdated libraries (SWL ignores them) "package"
# (the npm name and version, e.g. "jstree@3.3.17") or "own": true (our own file, not a
# library).
OPTIONAL_KEYS = ["integrity", "package", "own"]

# The resources of the frameworks SWL supports: see swl/frameworks.py
bootstrap_web_resources = (
    importlib.resources.files("swl.resources") / "bootstrap-web-resources.json"
)
web_resources = bootstrap_web_resources


def is_valid(data, mandatory, allowed):
    if not isinstance(data, dict):
        raise ValueError("Invalid data")

    for key in mandatory:
        if key not in data:
            raise ValueError(f"Missing {key} in style")

    data.setdefault("integrity", "")
    if len(set(data.keys()).difference(allowed)) > 0:
        raise ValueError("Invalid key in style")

    return True


def _load(path):
    if isinstance(path, str):
        path = pathlib.Path(path)
    return {} if path is None else json.loads(path.read_text())


def _replace_icons(styles, icons_stylesheet):
    if icons_stylesheet is not False:
        icons_stylesheet = dict(icons_stylesheet, icons=True)
        is_valid(
            icons_stylesheet, mandatory=["href"], allowed=["href", "integrity", "icons"]
        )
    result, replaced = [], False
    for style in styles:
        if not style.get("icons"):
            result.append(style)
        elif not replaced:
            replaced = True
            if icons_stylesheet is not False:
                result.append(icons_stylesheet)
    if not replaced and icons_stylesheet is not False:
        result.append(icons_stylesheet)  # resources without an icon font of their own
    return result


class WebResources:
    """The styles and scripts swl/base.j2 loads: those in path (a JSON file with "styles"
    and "scripts"), followed by those in each of the extra files (e.g. a library only some
    applications use).

    The style with "icons": true is the icon font (Bootstrap Icons in SWL's own files).
    icons_stylesheet replaces it: a style ({"href": ..., "integrity": ...}), or False to
    leave it out; None keeps it (swl/icons.py)."""

    def __init__(self, path=None, base_url=None, extra=(), icons_stylesheet=None):
        confs = [_load(path or web_resources)]
        if isinstance(extra, (str, pathlib.PurePath)):
            extra = [extra]
        confs.extend(_load(each) for each in extra or ())

        styles = [
            style
            for conf in confs
            for style in conf.get("styles", [])
            if is_valid(
                style, mandatory=["href"], allowed=["href", "icons", *OPTIONAL_KEYS]
            )
        ]
        if icons_stylesheet is not None:
            styles = _replace_icons(styles, icons_stylesheet)
        self._styles = [
            {**style, "href": style["href"].format(BASE_URL=base_url)} for style in styles
        ]
        self._scripts = [
            {**script, "src": script["src"].format(BASE_URL=base_url)}
            for conf in confs
            for script in conf.get("scripts", [])
            if is_valid(script, mandatory=["src"], allowed=["src", *OPTIONAL_KEYS])
        ]

    @property
    def styles(self):
        return self._styles

    @property
    def scripts(self):
        return self._scripts
