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

from types import SimpleNamespace

import pytest

from .menu import Menu, MenuItem


def request(path="/", scopes=(), admin=False):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        auth=SimpleNamespace(scopes=list(scopes)),
        user=SimpleNamespace(admin=admin),
    )


def test_a_url_or_an_action():
    MenuItem("Tasks", url="/tasks")
    MenuItem("Users", action="users_show")
    with pytest.raises(ValueError):
        MenuItem("Nothing")
    with pytest.raises(ValueError):
        MenuItem("Both", url="/", action="users_show")


def test_available():
    assert MenuItem("Tasks", url="/").available(request())
    item = MenuItem("Users", action="users_show", scope="role:admin")
    assert not item.available(request(scopes=["authenticated"]))
    assert item.available(request(scopes=["authenticated", "role:admin"]))
    item = MenuItem("Users", action="users_show", check=lambda r: r.user.admin)
    assert not item.available(request())
    assert item.available(request(admin=True))


def test_available_without_authentication():
    class NoAuth:
        url = SimpleNamespace(path="/")

        @property
        def auth(self):
            raise AssertionError("AuthenticationMiddleware must be installed")

    assert MenuItem("Tasks", url="/").available(NoAuth())
    assert not MenuItem("Users", url="/u", scope="role:admin").available(NoAuth())


def test_current():
    tasks = MenuItem("Tasks", url="/tasks")
    assert tasks.current(request("/tasks"))
    assert tasks.current(request("/tasks/12/details"))
    assert not tasks.current(request("/tasksx"))
    assert not tasks.current(request("/"))
    home = MenuItem("Home", url="/")
    assert home.current(request("/"))
    assert not home.current(request("/tasks"))
    assert not MenuItem("Users", action="users_show").current(request("/"))


def test_for_request():
    menu = Menu(
        title="App",
        main=[MenuItem("Tasks", url="/")],
        admin=[MenuItem("Users", action="users_show", scope="role:admin")],
        user=[MenuItem("Log out", url="/logout")],
    )
    for_user = menu.for_request(request(scopes=["authenticated"]))
    assert for_user.title == "App"
    assert [item.label for item in for_user.main] == ["Tasks"]
    assert for_user.admin == []
    assert [item.label for item in for_user.user] == ["Log out"]
    assert for_user.admin_label == "Manage"
    for_admin = menu.for_request(request(scopes=["role:admin"]))
    assert [item.label for item in for_admin.admin] == ["Users"]


def test_an_empty_menu():
    menu = Menu().for_request(request())
    assert menu == ("", [], [], "Manage", [])
