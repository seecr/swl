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
from .routes_endpoint import _parse_networks, make_routes_route, routes_route


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


@pytest.mark.parametrize(
    "allowlist", ["192.168.0.0/16, 2001:db8::1", ["192.168.0.0/16", "2001:db8::1"]]
)
@pytest.mark.parametrize(
    "ip, status",
    [
        ("192.168.1.2", 200),
        ("2001:db8::1", 200),
        ("127.0.0.1", 404),  # in ALLOWED_NETWORKS, but not in this allow list
        ("10.1.2.3", 404),
    ],
)
def test_own_allowlist(allowlist, ip, status):
    app = Starlette(routes=[Route("/", ok), make_routes_route(allowlist)])
    client = TestClient(app, client=(ip, 50000))
    response = client.get("/.routes")
    assert response.status_code == status
    if status == 200:
        assert [r["path"] for r in response.json()["routes"]] == ["/", "/.routes"]


def test_empty_allowlist_allows_nobody():
    app = Starlette(routes=[make_routes_route([])])
    client = TestClient(app, client=("127.0.0.1", 50000))
    assert client.get("/.routes").status_code == 404


def make_swl():
    from seecr_stdlib.config import Config

    from .swl import SWL

    swl = SWL(config=Config({}))
    swl.register_action_kwargs(slugs=["first-project", "second.project"])
    return swl


async def page(request, **kwargs):
    return PlainTextResponse(request.path_params["slug"])


def slug_paths(request, slugs, **kwargs):
    return ["/" + slug for slug in slugs]


async def async_slug_paths(request, slugs, **kwargs):
    return slug_paths(request, slugs)


@pytest.mark.parametrize("paths", [slug_paths, async_slug_paths])
def test_route_with_own_paths(paths):
    swl = make_swl()
    app = Starlette(
        routes=[
            routes_route,
            Mount(
                "/p",
                routes=[
                    Route(
                        "/{slug}",
                        swl.endpoint(page, authenticated=False, paths=paths),
                        name="project",
                    )
                ],
            ),
            Route("/{other}", swl.endpoint(page, authenticated=False)),
        ]
    )
    client = TestClient(app, client=("127.0.0.1", 50000))
    routes = client.get("/.routes").json()["routes"]
    project = [r for r in routes if r["name"] == "project"]
    assert [r["path"] for r in project] == ["/p/first-project", "/p/second.project"]
    for r in project:
        assert r["type"] == "http"
        assert r["static"] is True
        assert r["methods"] is None  # an ASGI app (swl.endpoint): any method
    assert matches(project[1], "/p/second.project")
    assert not matches(project[1], "/p/secondxproject")  # the dot is not a wildcard
    assert not matches(project[0], "/p/other")
    assert "/{other}" in [r["path"] for r in routes]  # without paths: the pattern
    assert client.get("/p/first-project").text == "first-project"
