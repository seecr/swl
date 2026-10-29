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

import re

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.testclient import TestClient

from . import routes_endpoint
from .routes_endpoint import _parse_networks, routes_route


async def ok(request):
    return PlainTextResponse("ok")


@pytest.fixture
def app():
    return Starlette(
        routes=[
            Route("/", ok),
            Route("/users/{user_id:int}", ok, methods=["GET", "DELETE"]),
            Mount(
                "/api",
                routes=[
                    Route("/health", ok),
                    Mount("/v1", routes=[Route("/items/{item_id}", ok)]),
                ],
            ),
            Mount(
                "/static",
                app=StaticFiles(directory=".", check_dir=False),
                name="static",
            ),
            routes_route,
        ]
    )


@pytest.fixture(autouse=True)
def allowlist(monkeypatch):
    monkeypatch.setattr(
        routes_endpoint, "ALLOWED_NETWORKS", _parse_networks("127.0.0.1,10.0.0.0/8")
    )


@pytest.fixture
def routes(app):
    client = TestClient(app, client=("127.0.0.1", 50000))
    response = client.get("/.routes")
    assert response.status_code == 200
    return {r["path"]: r for r in response.json()["routes"]}


def matches(route, path):
    return re.fullmatch(route["regex"], path) is not None


def test_plain_route(routes):
    r = routes["/"]
    assert r["type"] == "http"
    assert r["static"] is True
    assert r["methods"] == ["GET", "HEAD"]
    assert matches(r, "/")
    assert not matches(r, "/other")


def test_route_with_path_parameter(routes):
    r = routes["/users/{user_id}"]
    assert r["static"] is False
    assert r["methods"] == ["DELETE", "GET", "HEAD"]
    assert matches(r, "/users/42")
    assert not matches(r, "/users/abc")  # :int convertor
    assert not matches(r, "/users/42/extra")


def test_mount_with_routes_is_flattened(routes):
    assert "/api/health" in routes
    assert routes["/api/health"]["static"] is True
    nested = routes["/api/v1/items/{item_id}"]
    assert matches(nested, "/api/v1/items/abc")
    assert not matches(nested, "/items/abc")
    assert "/api" not in routes and "/api/" not in routes  # no separate mount entry


def test_mount_with_app_is_prefix(routes):
    r = routes["/static/"]
    assert r["type"] == "mount"
    assert r["methods"] is None
    assert matches(r, "/static/css/site.css")
    assert not matches(r, "/staticfoo")


def test_routes_endpoint_lists_itself(routes):
    assert routes["/.routes"]["methods"] == ["GET", "HEAD"]


@pytest.mark.parametrize(
    "ip, status",
    [
        ("127.0.0.1", 200),
        ("10.1.2.3", 200),
        ("8.8.8.8", 404),
        ("2001:db8::1", 404),
    ],
)
def test_ip_allowlist(app, ip, status):
    client = TestClient(app, client=(ip, 50000))
    assert client.get("/.routes").status_code == status
