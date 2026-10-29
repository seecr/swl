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

import json
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from swl import SWL, templates_dir
from swl.session import SessionAuthBackend
from swl.userbase import Userbase
from swl.views import account

from seecr_stdlib.config import Config

from . import VERSION


async def create_app(swl, userbase, routes=None):
    async def main_page(request):
        return PlainTextResponse(f"This is SWL {VERSION}")

    return Starlette(
        debug=True,
        routes=[
            swl.action_route,
            Route(
                "/login",
                name="login",
                endpoint=swl.endpoint(account.login, authenticated=False),
                methods=["POST"],
            ),
            Route(
                "/logout", endpoint=swl.endpoint(account.logout, authenticated=False)
            ),
        ]
        + (routes or [])
        + [
            Route("/", endpoint=main_page),
        ],
        middleware=[
            Middleware(SessionMiddleware, secret_key="SECRET_TEST_KEY"),
            Middleware(
                AuthenticationMiddleware, backend=SessionAuthBackend(userbase=userbase)
            ),
        ],
    )


@pytest.fixture
async def environment(tmp_path):
    this_directory = Path(__file__).parent

    userbase = Userbase.for_testing(tmp_path / "users")
    userbase.create("admin", "admin_password", admin=True)
    userbase.create("user", "user_password", admin=False)

    swl = SWL(
        config=Config({}), templates=[this_directory / "templates", templates_dir]
    )
    swl.register_modules(account)
    swl.register_action_kwargs(userbase=userbase)

    app = await create_app(swl, userbase)

    client = TestClient(app)
    login_user(client, "admin", "admin_password")

    return client, swl, userbase


def login_user(client, username, password):
    response = client.post("/login", data={"username": username, "password": password})
    assert_success(response)
    client.cookies.clear()
    client.cookies["session"] = response.cookies["session"]


def logout_user(client):
    response = client.get("/logout")
    assert response.status_code == 200
    client.cookies.clear()


def swl_events(response):
    """The SWL events of a response (its HX-Trigger header)."""
    return json.loads(response.headers.get("HX-Trigger", "{}"))


def assert_success(response):
    """Asserts a SuccessResponse and returns its events."""
    assert response.status_code in (200, 204), response.status_code
    return swl_events(response)


def assert_fail(response, message=None):
    """Asserts a FailResponse, optionally with the given message."""
    assert response.status_code == 422, response.status_code
    if message is not None:
        assert swl_events(response) == {"swl-error": {"message": message}}
