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

"""SWL's layouts (swl/templates/swl/layouts/), with the menu of swl.set_menu."""

import pytest
from seecr_stdlib.config import Config
from starlette.routing import Route
from starlette.testclient import TestClient

from swl import SWL
from swl.menu import MenuItem
from swl.test_utils import create_app, login_user
from swl.userbase import Userbase
from swl.views import account

LAYOUTS = ["sidebar", "topbar", "retro"]


async def page(request, swl, **kwargs):
    return swl.template_response(
        request,
        "page.j2",
        {"title": "Tasks", "layout": request.query_params["layout"]},
    )


@pytest.fixture
async def client(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.j2").write_text(
        '{% extends "swl/layouts/" ~ layout ~ ".j2" %}'
        "{% block toolbar %}<span id=tool>tool</span>{% endblock %}"
        "{% block content %}<p id=content>The page</p>{% endblock %}"
    )
    userbase = Userbase.for_testing(tmp_path / "users")
    userbase.create("admin", "admin_password", admin=True)
    userbase.create("user", "user_password", admin=False)

    swl = SWL(config=Config({}), templates=[templates])
    swl.register_modules(account)
    swl.register_action_kwargs(userbase=userbase)
    swl.add_template_globals(VERSION="test")
    swl.set_menu(
        title="Test App",
        main=[
            MenuItem("Tasks", url="/page", icon="bi bi-list"),
            MenuItem("Help", url="/help"),
        ],
        admin=[
            MenuItem(
                "Users",
                action="users_show",
                icon="bi bi-people",
                check=lambda request: request.user.admin,
            )
        ],
        user=[MenuItem("Log out", url="/logout")],
    )
    app = await create_app(
        swl, userbase, routes=[Route("/page", swl.endpoint(page, redirect="/login"))]
    )
    return TestClient(app), swl


@pytest.mark.parametrize("layout", LAYOUTS)
def test_a_layout_shows_the_page_and_the_menu(client, layout):
    client, swl = client
    login_user(client, "admin", "admin_password")
    html = client.get("/page", params={"layout": layout}).text
    assert f'class="swl-layout swl-layout-{layout}"' in html
    assert "/static/swl/swl-layouts.css" in html and "/static/swl/layouts.js" in html
    assert "<p id=content>The page</p>" in html
    assert "<span id=tool>tool</span>" in html
    assert "Test App" in html
    assert '<a href="/page" class="swl-layout-link" aria-current="page">' in html
    assert '<a href="/help" class="swl-layout-link">' in html
    assert f'hx-post="{swl.register("users_show")}"' in html  # admin only
    assert ">Manage<" in html
    assert '<a href="/logout"' in html and ">admin<" in html
    assert 'id="swl-modal"' in html  # the layout brings the dialog


@pytest.mark.parametrize("layout", LAYOUTS)
def test_the_menu_is_for_the_user(client, layout):
    client, swl = client
    login_user(client, "user", "user_password")
    html = client.get("/page", params={"layout": layout}).text
    assert swl.register("users_show") not in html
    assert ">Manage<" not in html  # no group without items
    assert '<a href="/help"' in html and ">user<" in html


def test_without_a_menu(tmp_path):
    """An app that does not call set_menu still gets the layout (an empty menu)."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.j2").write_text(
        '{% extends "swl/layouts/sidebar.j2" %}{% block content %}X{% endblock %}'
    )
    swl = SWL(config=Config({}), templates=[templates])
    swl.add_template_globals(VERSION="test")

    class Request:
        url = type("Url", (), {"path": "/"})()
        user = type("User", (), {"is_authenticated": False})()

    html = swl.template("page.j2").render(request=Request(), title="T")
    assert 'class="swl-layout swl-layout-sidebar"' in html and "X" in html
    assert "swl-layout-dropdown" not in html


@pytest.mark.parametrize("layout", LAYOUTS)
def test_the_layout_icons_are_named_icons(tmp_path, layout):
    """The layouts' own icons are SWL's named icons, so "ui.icons" changes them too."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.j2").write_text(
        f'{{% extends "swl/layouts/{layout}.j2" %}}{{% block content %}}X{{% endblock %}}'
    )
    swl = SWL(
        config=Config(
            {"ui": {"icons": {"menu": "ph ph-list", "start": "ph ph-windows-logo"}}}
        ),
        templates=[templates],
    )
    swl.add_template_globals(VERSION="test")
    swl.set_menu(main=[MenuItem("Tasks", url="/tasks")])  # topbar: a menu button

    class Request:
        url = type("Url", (), {"path": "/"})()
        user = type("User", (), {"is_authenticated": False})()
        auth = type("Auth", (), {"scopes": []})()

    html = swl.template("page.j2").render(request=Request(), title="T")
    assert "bi-list" not in html and "bi-windows" not in html
    if layout == "retro":
        assert '<i class="ph ph-windows-logo swl-icon"' in html
    else:
        assert '<i class="ph ph-list swl-icon"' in html
