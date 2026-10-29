## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from swl.test_utils import environment, create_app, login_user, logout_user

from .actions import Actions


@pytest.fixture
def write_module(tmp_path):
    import sys

    sys.path.insert(0, tmp_path.as_posix())

    def write_mod(name, text):
        (tmp_path / name).write_text(text)

    yield write_mod
    sys.path.pop(0)


def test_register_module_with_actions(tmp_path, write_module):
    actions = Actions()

    write_module("mod1.py", "def method1(x):\n  return 42")
    write_module("mod2.py", "def method2(x):\n  return 42\n__actions__ = [method2]")
    write_module(
        "mod3.py",
        "def method3(x):\n  return 42"
        + "\n__actions__ = [dict(method=method3, authenticated=False)]",
    )
    write_module(
        "mod4.py",
        "def method4(x):\n  return 42"
        + "\n__actions__ = [dict(method=method4, authenticated=True)]",
    )

    import mod1
    import mod2
    import mod3
    import mod4

    actions.register_module(mod1)
    assert len(actions._actions) == 0
    actions.register_module(mod2)
    assert len(actions._actions) == 1
    actions.register_module(mod3)
    assert len(actions._actions) == 2
    actions.register_module(mod4)
    assert len(actions._actions) == 3

    auth = [
        action
        for action in actions._actions.values()
        if action["is_allowed"].__doc__.startswith("authenticated=True")
    ]
    assert len(auth) == 2


async def test_default_auth(write_module):
    write_module("mod2.py", "def method2(x):\n return 42\n__actions__ = [method2]")
    import mod2

    auth_actions = Actions()
    auth_actions.register_module(mod2)
    assert list(auth_actions._actions.values())[0]["is_allowed"].__doc__.startswith(
        "authenticated=True"
    )

    noauth_actions = Actions(default_auth=False)
    noauth_actions.register_module(mod2)
    assert list(noauth_actions._actions.values())[0]["is_allowed"].__doc__.startswith(
        "authenticated=False"
    )


async def test_default_auth_with_dict(write_module):
    write_module(
        "mod2.py", "def method2(x):\n return 42\n__actions__ = [dict(method=method2)]"
    )
    import mod2

    auth_actions = Actions()
    auth_actions.register_module(mod2)
    assert list(auth_actions._actions.values())[0]["is_allowed"].__doc__.startswith(
        "authenticated=True"
    )

    noauth_actions = Actions(default_auth=False)
    noauth_actions.register_module(mod2)
    assert list(noauth_actions._actions.values())[0]["is_allowed"].__doc__.startswith(
        "authenticated=False"
    )


def test_register_with_different_path(write_module):
    write_module(
        "mod2.py", "def method2(x):\n return 42\n__actions__ = [dict(method=method2)]"
    )
    import mod2

    actions = Actions(path="/my/action", key=str.upper)
    actions.register_module(mod2)

    assert actions.register("method2") == "/my/action/METHOD2"
    with pytest.raises(RuntimeError):
        actions.register("unknown")
    assert actions.register("unknown", path="/other/action") == "/other/action/UNKNOWN"


async def test_is_authorized(environment):
    client, swl, userbase = environment

    async def some_action(request, **kwargs):
        return PlainTextResponse("Some Action")

    async def userbase_has_user2(request, userbase, **kwargs):
        return (userbase.get("user2")) is not None

    swl.actions.register_method(some_action, is_authorized=userbase_has_user2)

    response = client.post(swl.actions.register("some_action"))
    assert response.status_code == 403

    userbase.create("user2", "user2_password", admin=False)
    response = client.post(swl.actions.register("some_action"))
    assert response.status_code == 200
    assert response.text == "Some Action"


async def test_method_wrap(environment):
    _, swl, userbase = environment

    async def kwargs_page(request, **kwargs):
        kwarg_keys = sorted(kwargs.keys())
        return PlainTextResponse(f"Kwargs: {kwarg_keys}")

    app = await create_app(
        swl,
        userbase,
        routes=[
            Route("/wrapped", endpoint=swl.endpoint(kwargs_page)),
            Route("/unwrapped", endpoint=kwargs_page),
        ],
    )
    client = TestClient(app)
    login_user(client, "user", "user_password")

    response = client.get("/unwrapped")
    assert response.text == "Kwargs: []"

    response = client.get("/wrapped")
    assert response.text == "Kwargs: ['swl', 'userbase']"


async def test_wrap_authenticated(environment):
    _, swl, userbase = environment

    async def auth_page(request, **kwargs):
        return PlainTextResponse("Authenticated")

    async def is_admin(request, **kwargs):
        return request.user.admin

    async def login_page(request, **kwargs):
        return PlainTextResponse(request.session.get("next", "No next"))

    app = await create_app(
        swl,
        userbase,
        routes=[
            Route(
                "/auth",
                endpoint=swl.endpoint(
                    auth_page, authenticated=True, redirect="/login/here"
                ),
            ),
            Route(
                "/noauth",
                endpoint=swl.endpoint(auth_page, authenticated=False),
            ),
            Route(
                "/login/here",
                endpoint=swl.endpoint(login_page, authenticated=False),
            ),
            Route(
                "/admin_only",
                endpoint=swl.endpoint(
                    auth_page,
                    authenticated=True,
                    is_authorized=is_admin,
                    redirect="/login/here",
                ),
            ),
        ],
    )
    client = TestClient(app)

    response = client.get("/auth", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login/here"
    response = client.get("/login/here", follow_redirects=False)
    assert response.status_code == 200
    assert response.text == "/auth"

    login_user(client, "user", "user_password")
    response = client.get("/auth")
    assert response.status_code == 200
    assert response.text == "Authenticated"

    response = client.get("/admin_only", follow_redirects=False)
    assert response.status_code == 303
    response = client.get(response.headers["location"], follow_redirects=False)
    assert response.status_code == 200
    assert response.text == "/admin_only"

    login_user(client, "admin", "admin_password")
    response = client.get("/admin_only")
    assert response.status_code == 200
    assert response.text == "Authenticated"

    response = client.get("/noauth")
    assert response.status_code == 200
    assert response.text == "Authenticated"

    logout_user(client)
    response = client.get("/noauth")
    assert response.status_code == 200
    assert response.text == "Authenticated"
