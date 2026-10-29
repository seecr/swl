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

"""
The CSS framework an SWL application uses: "swl" (no framework, SWL's own swl-base.css),
"bootstrap", "tabler" (an admin design on top of Bootstrap) or "bulma". Choose it with the config key "ui.framework" (default "bootstrap").

The choice gives
  - the web resources (styles and scripts) that swl/base.j2 loads, and
  - a few CSS classes for form elements and buttons, as SWL.ui in templates, so that SWL's own
    templates (account and user screens) and your own can write
        <button class="{{ SWL.ui.button_primary }}">Save</button>
    and look right with each framework.

SWL's modal, message dialog, toast and context menu do not depend on the framework: they are
plain HTML styled by swl.css (and pick up the framework's colours).
"""

import contextvars
import importlib.resources
from http.cookies import CookieError, SimpleCookie
from dataclasses import dataclass, field
from types import MappingProxyType

_resources = importlib.resources.files("swl.resources")

# The class names SWL.ui offers; every framework defines all of them (empty: no class needed).
UI_CLASSES = (
    "input",           # <input> (text, password, search, ...)
    "select",          # <select>
    "textarea",        # <textarea>
    "checkbox",        # <input type="checkbox">
    "button",          # an ordinary button
    "button_primary",  # the main action (Save, Add)
    "button_danger",   # a destructive action (Delete)
    "small",           # added to a button: a small one
    "table",           # <table>
)


@dataclass(frozen=True)
class Framework:
    name: str
    resources: object  # a path (Traversable) to a resources JSON file
    classes: MappingProxyType = field(default_factory=dict)

    def __post_init__(self):
        missing = set(UI_CLASSES).difference(self.classes)
        if missing:
            raise ValueError(f"Framework {self.name!r} misses ui classes {sorted(missing)}")
        object.__setattr__(self, "classes", MappingProxyType(dict(self.classes)))


_BOOTSTRAP_CLASSES = {
    "input": "form-control",
    "select": "form-select",
    "textarea": "form-control",
    "checkbox": "form-check-input",
    "button": "btn btn-outline-secondary",
    "button_primary": "btn btn-primary",
    "button_danger": "btn btn-outline-danger",
    "small": "btn-sm",
    "table": "table align-middle",
}

FRAMEWORKS = {
    "swl": Framework(
        name="swl",
        resources=_resources / "swl-web-resources.json",
        classes={
            "input": "",
            "select": "",
            "textarea": "",
            "checkbox": "",
            "button": "",
            "button_primary": "primary",
            "button_danger": "danger",
            "small": "small",
            "table": "",
        },
    ),
    "bootstrap": Framework(
        name="bootstrap",
        resources=_resources / "bootstrap-web-resources.json",
        classes=_BOOTSTRAP_CLASSES,
    ),
    # Tabler is built on Bootstrap 5: the same classes, its own look (and its own javascript bundle,
    # which includes Bootstrap's)
    "tabler": Framework(
        name="tabler",
        resources=_resources / "tabler-web-resources.json",
        classes=_BOOTSTRAP_CLASSES,
    ),
    "bulma": Framework(
        name="bulma",
        resources=_resources / "bulma-web-resources.json",
        classes={
            "input": "input",
            "select": "",
            "textarea": "textarea",
            "checkbox": "",
            "button": "button",
            "button_primary": "button is-primary",
            "button_danger": "button is-danger is-outlined",
            "small": "is-small",
            "table": "table is-fullwidth",
        },
    ),
}

DEFAULT_FRAMEWORK = "bootstrap"


def framework(name=None):
    """The Framework for a name (None: the default)."""
    name = name or DEFAULT_FRAMEWORK
    try:
        return FRAMEWORKS[name]
    except KeyError:
        raise ValueError(
            f"Unknown ui.framework {name!r}; choose one of {', '.join(sorted(FRAMEWORKS))}"
        ) from None


# The framework chosen for the current request (FrameworkCookieMiddleware); None: the default.
_requested = contextvars.ContextVar("swl_requested_framework", default=None)


def requested_framework():
    """The Framework chosen for the current request, or None."""
    return FRAMEWORKS.get(_requested.get() or "")


class FrameworkCookieMiddleware:
    """
    ASGI middleware that lets a visitor choose the CSS framework with a cookie, e.g. for a demo or a
    style guide: a cookie `cookie` with a framework name ("swl", "bootstrap", ...) overrides "ui.framework"
    for that request. Anything else in the cookie is ignored.

        app = Starlette(..., middleware=[Middleware(FrameworkCookieMiddleware)])

    In the browser: document.cookie = "swl_framework=bulma; path=/"; location.reload();
    """

    def __init__(self, app, cookie="swl_framework"):
        self.app = app
        self.cookie = cookie

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        token = _requested.set(self._from_cookie(scope))
        try:
            await self.app(scope, receive, send)
        finally:
            _requested.reset(token)

    def _from_cookie(self, scope):
        for key, value in scope.get("headers", []):
            if key == b"cookie":
                cookies = SimpleCookie()
                try:
                    cookies.load(value.decode("latin-1"))
                except CookieError:
                    return None
                morsel = cookies.get(self.cookie)
                if morsel is not None and morsel.value in FRAMEWORKS:
                    return morsel.value
        return None
