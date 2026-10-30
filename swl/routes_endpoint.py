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
A `/.routes` endpoint for Starlette that lists every route the app handles.

Only clients whose IP is in the allow list get an answer; everyone else gets a
plain 404 so the endpoint's existence is not revealed. The allow list holds
IPs/CIDRs, e.g. "127.0.0.1,10.0.0.0/8,::1". SWL's `swl.routes_route` takes it
from the config key `routes.allowlist`, otherwise from ROUTES_ALLOWLIST
(default "127.0.0.1,::1").

IMPORTANT when running behind Traefik: request.client.host is Traefik's IP
unless the ASGI server is told to trust Traefik's X-Forwarded-For header, e.g.

    uvicorn app:app --proxy-headers --forwarded-allow-ips=<traefik-ip>

Never use --forwarded-allow-ips='*' if the app port is reachable directly,
because then anyone can spoof their address.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Iterable

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import (
    BaseRoute,
    Host,
    Mount,
    Route,
    WebSocketRoute,
    compile_path,
)


def _parse_networks(value: str | Iterable[str]) -> list[ipaddress._BaseNetwork]:
    parts = value.split(",") if isinstance(value, str) else value
    return [
        ipaddress.ip_network(part.strip(), strict=False)
        for part in parts
        if part.strip()
    ]


ALLOWED_NETWORKS = _parse_networks(os.environ.get("ROUTES_ALLOWLIST", "127.0.0.1,::1"))


def client_allowed(request: Request, networks=None) -> bool:
    networks = ALLOWED_NETWORKS if networks is None else networks
    host = request.client.host if request.client else None
    try:
        ip = ipaddress.ip_address(host)
    except (TypeError, ValueError):
        return False
    if ip.version == 6 and ip.ipv4_mapped:  # ::ffff:1.2.3.4 -> 1.2.3.4
        ip = ip.ipv4_mapped
    return any(ip in net for net in networks)


def collect_routes(
    routes: Iterable[BaseRoute], prefix: str = "", host: str | None = None
) -> list[dict]:
    """Flatten (possibly nested) Starlette routes into a list of dicts.

    Each entry has:
      path    - the path format, e.g. "/users/{user_id}"
      regex   - an anchored regex for the full path (RE2/Go compatible,
                so Traefik can use it directly in PathRegexp)
      static  - True when the path has no parameters (exact match is enough)
      methods - allowed HTTP methods, or null for "any"
      type    - "http", "websocket" or "mount"
      host    - Host constraint from a starlette Host() route, or null
    """
    found: list[dict] = []
    for route in routes:
        if isinstance(route, Mount):
            mount_path = prefix + route.path
            children = (
                route.routes
            )  # [] when the mounted app is not a router (e.g. StaticFiles)
            if children:
                found.extend(collect_routes(children, mount_path, host))
            else:
                regex, fmt, _ = compile_path(mount_path + "/{path:path}")
                found.append(
                    {
                        "type": "mount",
                        "path": (mount_path or "") + "/",
                        "regex": regex.pattern,
                        "static": False,
                        "methods": None,
                        "host": host,
                        "name": route.name,
                    }
                )
        elif isinstance(route, Host):
            found.extend(collect_routes(route.routes, prefix, route.host))
        elif isinstance(route, (Route, WebSocketRoute)):
            full = prefix + route.path
            regex, fmt, convertors = compile_path(full)
            methods = sorted(getattr(route, "methods", None) or []) or None
            found.append(
                {
                    "type": (
                        "websocket" if isinstance(route, WebSocketRoute) else "http"
                    ),
                    "path": fmt,
                    "regex": regex.pattern,
                    "static": not convertors,
                    "methods": methods,
                    "host": host,
                    "name": route.name,
                }
            )
    return found


def make_routes_route(allowlist: str | Iterable[str] | None = None) -> Route:
    """Return the `/.routes` route, answering only clients in `allowlist`.

    `allowlist`: IPs/CIDRs as a comma-separated string or a list.
    None: use ALLOWED_NETWORKS (from ROUTES_ALLOWLIST).
    """
    networks = None if allowlist is None else _parse_networks(allowlist)

    async def list_routes(request: Request):
        if not client_allowed(request, networks):
            return PlainTextResponse("Not Found", status_code=404)
        return JSONResponse({"routes": collect_routes(request.app.routes)})

    return Route("/.routes", list_routes, methods=["GET"], name=".routes")


routes_route = make_routes_route()
list_routes = routes_route.endpoint
