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

"""The menu of an app, for SWL's layouts (swl/templates/swl/layouts/):

    swl.set_menu(
        title="My App",
        main=[MenuItem(N_("Tasks"), url="/", icon="bi-check2-square")],
        admin=[MenuItem(N_("Users"), action="users_show", scope="role:admin")],
        user=[MenuItem(N_("Log out"), url="/logout", icon="bi-box-arrow-right")],
    )

"main" is the menu itself, "admin" a group of its own (under "Manage"), "user" the menu
of the logged-in user. A layout shows each item that is available to the request, its
label translated with _()."""

from dataclasses import dataclass
from typing import Callable, NamedTuple

from .i18n import N_

__all__ = ["MenuItem", "Menu"]


@dataclass(frozen=True)
class MenuItem:
    """A link (url) or an SWL action (action, e.g. one that opens a dialog).

    scope: shown only when the request has this scope (request.auth.scopes, as the
    authentication backend sets them); check: shown only when check(request) is true.
    icon: a Bootstrap Icons class, e.g. "bi-people"."""

    label: str
    url: str = None
    action: str = None
    icon: str = None
    scope: str = None
    check: Callable = None

    def __post_init__(self):
        if (self.url is None) == (self.action is None):
            raise ValueError(f"MenuItem {self.label!r}: give a url or an action")

    def available(self, request):
        if self.scope is not None and self.scope not in _scopes(request):
            return False
        return self.check is None or bool(self.check(request))

    def current(self, request):
        """Whether this is the page of the request: its url, or a page below it."""
        if self.url is None:
            return False
        path = request.url.path
        if self.url == "/":
            return path == "/"
        return path == self.url or path.startswith(self.url.rstrip("/") + "/")


class MenuFor(NamedTuple):
    """The menu for one request: only the items that are available to it."""

    title: str
    main: list
    admin: list
    admin_label: str
    user: list


class Menu:
    def __init__(self, title="", main=(), admin=(), user=(), admin_label=N_("Manage")):
        self.title = title
        self.main = list(main)
        self.admin = list(admin)
        self.user = list(user)
        self.admin_label = admin_label

    def for_request(self, request):
        def available(items):
            return [item for item in items if item.available(request)]

        return MenuFor(
            title=self.title,
            main=available(self.main),
            admin=available(self.admin),
            admin_label=self.admin_label,
            user=available(self.user),
        )


def _scopes(request):
    try:
        return request.auth.scopes
    except AssertionError:  # no AuthenticationMiddleware
        return []
