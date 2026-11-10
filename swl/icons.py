## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

"""
The icons in SWL's own templates and swl.js, by name. By default Bootstrap Icons (its
stylesheet is in the web resources of every framework); an application with its own
icon set gives its own classes for SWL's names, with the config key "ui.icons":

    "ui": {
        "icons": {"close": "ph-light ph-x", "confirm": "ph-fill ph-question", ...},
        "icons_stylesheet": {"href": "/static/phosphor/style.css"}
    }

A name that is not given keeps its Bootstrap icon; an unknown name is an error (a typo
would otherwise go unnoticed). "ui.icons_stylesheet" replaces the Bootstrap Icons
stylesheet in the web resources ({"href": ..., "integrity": ...}), or, with false, leaves
it out (the application loads its icons itself).

In templates: <i class="{{ SWL.icons.close }} swl-icon" aria-hidden="true"></i>. swl.js
reads them from <script type="application/json" id="swl-icons"> (swl/base.j2).

The older Bootstrap pieces (swl/card.j2, swl/breadcrumbs.j2) keep Bootstrap's icons.
"""

from types import MappingProxyType

BOOTSTRAP_ICONS = MappingProxyType(
    {
        # dialogs (swl/modal-content.j2, swl/dialog.j2, swl.js)
        "close": "bi bi-x-lg",
        "confirm": "bi bi-question-diamond-fill",
        "error": "bi bi-exclamation-circle-fill",
        "info": "bi bi-info-circle-fill",
        "yes": "bi bi-check-lg",
        "no": "bi bi-x-lg",
        # "Saved" after a save (data-swl-saved, swl.js)
        "saved": "bi bi-check2",
        # account and users (swl/account*.j2, swl/users*.j2)
        "user": "bi bi-person-fill",
        "users": "bi bi-people",
        "user_list": "bi bi-person-lines-fill",
        "user_add": "bi bi-person-plus",
        "add": "bi bi-plus-lg",
        "delete": "bi bi-trash",
        "password": "bi bi-key",
        "save": "bi bi-check2",
        "note": "bi bi-info-circle",
    }
)


def icons(overrides=None):
    """SWL's icons: the Bootstrap ones, with the classes in overrides (a dict of name:
    classes) instead."""
    overrides = dict(overrides or {})
    unknown = set(overrides).difference(BOOTSTRAP_ICONS)
    if unknown:
        raise ValueError(
            f"Unknown icon names {sorted(unknown)}; known: {sorted(BOOTSTRAP_ICONS)}"
        )
    for name, classes in overrides.items():
        if not isinstance(classes, str) or not classes.strip():
            raise ValueError(f"Icon {name!r}: classes should be a non-empty string")
    return MappingProxyType({**BOOTSTRAP_ICONS, **overrides})
