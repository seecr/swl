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


class WebResources:
    def __init__(self, path=None, base_url=None):
        path = path or web_resources
        if isinstance(path, str):
            path = pathlib.Path(path)
        conf = {} if path is None else json.loads(path.read_text())

        self._styles = [
            {**style, "href": style["href"].format(BASE_URL=base_url)}
            for style in conf.get("styles", [])
            if is_valid(style, mandatory=["href"], allowed=["href", "integrity"])
        ]
        self._scripts = [
            {**script, "src": script["src"].format(BASE_URL=base_url)}
            for script in conf.get("scripts", [])
            if is_valid(script, mandatory=["src"], allowed=["src", "integrity"])
        ]

    @property
    def styles(self):
        return self._styles

    @property
    def scripts(self):
        return self._scripts
