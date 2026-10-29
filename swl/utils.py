## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

from urllib.parse import urlencode
import importlib


def url(location, **params):
    return location if len(params) == 0 else "{}?{}".format(location, urlencode(params))


class Views:
    def __init__(self, name, view_list):
        self._views = {
            view_name: importlib.import_module("." + view_name, name)
            for view_name in view_list
        }

    @property
    def modules(self):
        return self._views.values()

    def __getattr__(self, key):
        if key in self._views:
            return self._views[key]
        return super().__getattribute__(key)
