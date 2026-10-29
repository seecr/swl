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

import uuid

from starlette.applications import Starlette
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from swl.swl import SWL


class TestUser(BaseUser):
    @property
    def display_name(self):
        return "TestUser"

    @property
    def is_authenticated(self):
        return True


class TestAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "user" in conn.session:
            return AuthCredentials(["authenticated"]), TestUser()


async def authenticated_method(request, swl):
    return swl.success()


async def unauthenticated_method(request, swl):
    return swl.success()


async def page(request, swl, **kwargs):
    return PlainTextResponse(f"Authenticated: {request.user.is_authenticated}")


async def login(request, swl, **kwargs):
    request.session["user"] = True
    return PlainTextResponse("OK")


async def logout(request, swl, **kwargs):
    request.session.clear()
    return PlainTextResponse("OK")


async def test_auth(tmp_path):

    swl = SWL(config={})
    swl.actions.register_method(authenticated_method)
    swl.actions.register_method(unauthenticated_method, authenticated=False)

    app = Starlette(
        routes=[
            swl.action_route,
            Route("/secure", endpoint=swl.endpoint(page)),
            Route(
                "/unsecure",
                endpoint=swl.endpoint(page, authenticated=False, redirect="/login"),
            ),
            Route("/login", endpoint=swl.endpoint(login, authenticated=False)),
            Route("/logout", endpoint=swl.endpoint(logout, authenticated=False)),
        ],
        middleware=[
            Middleware(SessionMiddleware, secret_key=str(uuid.uuid1())),
            Middleware(
                AuthenticationMiddleware,
                backend=TestAuthBackend(),
            ),
        ],
    )

    client = TestClient(app)
    response = client.post("/secure")
    assert response.status_code == 403

    response = client.post("/unsecure")
    assert response.status_code == 200
    assert response.text == "Authenticated: False"

    response = client.post(swl.actions.register("authenticated_method"))
    assert response.status_code == 403

    response = client.post(swl.actions.register("unauthenticated_method"))
    assert response.status_code == 204  # empty SuccessResponse

    response = client.get("/login")
    assert response.status_code == 200

    response = client.post("/secure")
    assert response.status_code == 200
    assert response.text == "Authenticated: True"

    response = client.post("/unsecure")
    assert response.status_code == 200
    assert response.text == "Authenticated: True"

    response = client.post(swl.actions.register("authenticated_method"))
    assert response.status_code == 204  # empty SuccessResponse

    response = client.post(swl.actions.register("unauthenticated_method"))
    assert response.status_code == 204  # empty SuccessResponse
