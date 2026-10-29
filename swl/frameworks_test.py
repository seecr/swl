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

import json

import pytest

from seecr_stdlib.config import Config

from swl import SWL
from swl.frameworks import FRAMEWORKS, UI_CLASSES, Framework, framework


def _swl(**ui):
    return SWL(config=Config({"ui": ui} if ui else {}))


def test_default_is_bootstrap():
    swl = _swl()
    assert swl.framework == "bootstrap"
    assert any("bootstrap.min.css" in s["href"] for s in swl.styles)
    assert any("bootstrap.bundle.min.js" in s["src"] for s in swl.scripts)
    assert swl.ui["button_primary"] == "btn btn-primary"


@pytest.mark.parametrize(
    "name, css",
    [
        ("swl", "/static/swl/swl-base.css"),
        ("bootstrap", "bootstrap.min.css"),
        ("tabler", "tabler.min.css"),
        ("bulma", "bulma.min.css"),
    ],
)
def test_framework_resources(name, css):
    swl = _swl(framework=name)
    assert swl.framework == name
    hrefs = [s["href"] for s in swl.styles]
    assert any(css in href for href in hrefs)
    assert any("bootstrap-icons" in href for href in hrefs), "icons with every framework"
    assert any("htmx.org@4.0.0" in s["src"] for s in swl.scripts)
    assert set(swl.ui) == set(UI_CLASSES)


def test_default_resources_come_from_jsdelivr_with_integrity():
    for fw in FRAMEWORKS.values():
        conf = json.loads(fw.resources.read_text())
        for item in conf["styles"] + conf["scripts"]:
            url = item.get("href") or item.get("src")
            if url.startswith("/static/"):
                continue
            assert url.startswith("https://cdn.jsdelivr.net/npm/"), url
            assert item.get("integrity", "").startswith("sha384-"), url


def test_unknown_framework():
    with pytest.raises(ValueError, match="choose one of bootstrap, bulma, swl, tabler"):
        _swl(framework="tailwind")


def test_own_resources_replace_the_frameworks(tmp_path):
    (path := tmp_path / "res.json").write_text(
        json.dumps({"styles": [{"href": "mine.css"}]})
    )
    swl = SWL(
        config=Config(
            {"ui": {"framework": "bulma"}, "paths": {"resources": str(path)}}
        )
    )
    assert [s["href"] for s in swl.styles] == ["mine.css"]
    assert swl.ui["button"] == "button", "the classes still follow the framework"


def test_a_framework_must_define_every_class():
    with pytest.raises(ValueError, match="misses ui classes"):
        Framework(name="x", resources=None, classes={"input": ""})


def test_templates_get_the_classes():
    swl = _swl(framework="bulma")
    html = swl.template("swl/account_password.j2").render(
        user={"username": "u"}, register=lambda name: "/action/" + name
    )
    assert 'class="input"' in html and 'class="button is-primary"' in html


def _app(swl, cookie=None):
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from swl.frameworks import FrameworkCookieMiddleware

    async def page(request):
        return JSONResponse({"framework": swl.framework, "button": swl.ui["button"],
                             "styles": [s["href"] for s in swl.styles]})

    app = Starlette(
        routes=[Route("/", page)], middleware=[Middleware(FrameworkCookieMiddleware)]
    )
    client = TestClient(app)
    if cookie is not None:
        client.cookies.set("swl_framework", cookie)
    return client.get("/").json()


def test_a_cookie_chooses_the_framework_per_request():
    swl = _swl(framework="swl")
    assert _app(swl)["framework"] == "swl"
    result = _app(swl, "bulma")
    assert result["framework"] == "bulma" and result["button"] == "button"
    assert any("bulma.min.css" in href for href in result["styles"])
    assert _app(swl, "bootstrap")["framework"] == "bootstrap"
    assert _app(swl, "tailwind")["framework"] == "swl", "unknown: the default"
    assert swl.framework == "swl", "outside a request: the default"


def test_tabler_is_bootstrap_with_its_own_look():
    swl = _swl(framework="tabler")
    assert dict(swl.ui) == dict(_swl(framework="bootstrap").ui)
    assert any("@tabler/core" in s["src"] for s in swl.scripts)
    assert not any(
        "bootstrap.bundle" in s["src"] for s in swl.scripts
    ), "Tabler's bundle includes Bootstrap's"
