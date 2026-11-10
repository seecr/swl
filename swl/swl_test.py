## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2025 Seecr (Seek You Too B.V.) https://seecr.nl
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
from starlette.applications import Starlette
from starlette.testclient import TestClient

from .swl import SWL


def test_swl(tmp_path):
    (conf_path := tmp_path / "test.json").write_text(
        json.dumps(
            {
                "styles": [{"href": "test.css", "integrity": "sha256-123"}],
                "scripts": [
                    {"src": "test.js"},
                ],
            }
        )
    )
    swl = SWL(
        config=Config(
            {"urls": {"cdn": "http://example.com"}, "paths": {"resources": conf_path}}
        )
    )
    assert swl.styles[0]["href"] == "test.css"
    # assert swl.web_resources.base_url == "http://example.com"


def test_swl_extra_resources(tmp_path):
    conf_path = tmp_path / "extra.json"
    conf_path.write_text(json.dumps({"scripts": [{"src": "extra.js"}]}))
    swl = SWL(
        config=Config(
            {"ui": {"framework": "swl"}, "paths": {"extra_resources": [conf_path]}}
        )
    )
    assert swl.scripts[0]["src"].endswith("htmx.min.js")
    assert swl.scripts[-1]["src"] == "extra.js"


def test_swl_default():
    swl = SWL(config=Config({}))
    assert len(swl.styles) == 2
    # assert swl.web_resources.base_url == ""


def test_password_managers_ignore():
    # only the password managers' own opt-out attributes: no placeholder, which a
    # field would show as its hint text
    swl = SWL(config=Config({}))
    assert str(swl.password_managers_ignore) == (
        'data-1p-ignore data-lpignore="true" data-bwignore data-form-type="other" '
        "data-protonpass-ignore"
    )


def test_swl_route_path():
    def monkey():
        pass

    swl = SWL(config=Config({}))
    swl.actions.register_method(monkey)
    action = swl.register("monkey")
    assert action == "/action/d0763edaa9d9bd2a9516280e9044d885"
    assert swl.action_route.path == "/action/{action:str}"

    swl = SWL(config=Config({"actions": {"path": "/go_here"}}))
    swl.actions.register_method(monkey)
    action = swl.register("monkey")
    assert action == "/go_here/d0763edaa9d9bd2a9516280e9044d885"
    assert swl.action_route.path == "/go_here/{action:str}"


def test_swl_route_hash():
    def monkey():
        pass

    swl = SWL(config=Config({}))
    swl.actions.register_method(monkey)
    action = swl.register("monkey")
    assert action == "/action/d0763edaa9d9bd2a9516280e9044d885"

    swl = SWL(config=Config({"actions": {"hash": False}}))
    swl.actions.register_method(monkey)
    action = swl.register("monkey")
    assert action == "/action/monkey"


def test_jinja2_templates():
    swl = SWL(config=Config({}), templates=[])

    assert swl._templates.env.globals["SWL"] == swl
    assert swl._templates.env.globals["register"] == swl.actions.register


def test_kickstart_template():
    swl = SWL(config=Config({}))
    template = swl.template("swl/kickstart.j2")
    assert template.render().strip() == ""

    html = template.render(
        kickstart={"action": "/action/abc", "kwargs": {"qid": "Order:1"}}
    )
    assert 'swl.kickstart("/action/abc", {"qid": "Order:1"})' in html

    # values from a url end up here: they must not be able to break out of the script
    html = template.render(
        kickstart={
            "action": "/action/abc",
            "kwargs": {"q": "</script><script>alert(1)"},
        }
    )
    assert "</script><script>" not in html
    assert "\\u003c/script\\u003e" in html

    html = template.render(
        kickstart={"action": "/action/abc", "kwargs": '{"qid": "Order:1"}'}
    )
    assert 'swl.kickstart("/action/abc", "{\\"qid\\": \\"Order:1\\"}")' in html


@pytest.mark.parametrize(
    "config, ip, status",
    [
        ({"routes": {"allowlist": "10.0.0.0/8"}}, "10.1.2.3", 200),
        ({"routes": {"allowlist": ["10.0.0.0/8"]}}, "10.1.2.3", 200),
        ({"routes": {"allowlist": "10.0.0.0/8"}}, "127.0.0.1", 404),
        ({}, "127.0.0.1", 200),  # no config: ROUTES_ALLOWLIST or its default
        ({}, "10.1.2.3", 404),
    ],
)
def test_routes_route_allowlist_from_config(config, ip, status):
    swl = SWL(config=Config(config))
    client = TestClient(Starlette(routes=[swl.routes_route]), client=(ip, 50000))
    assert client.get("/.routes").status_code == status


def test_icons_default_bootstrap():
    swl = SWL(config=Config({}))
    assert swl.icons["close"] == "bi bi-x-lg"
    assert any("bootstrap-icons" in style["href"] for style in swl.styles)
    html = swl.template("swl/modal-content.j2").render()
    assert '<i class="bi bi-x-lg swl-icon" title="Close"></i>' in html


def test_icons_of_the_application():
    swl = SWL(
        config=Config(
            {
                "ui": {
                    "icons": {"close": "ph-light ph-x", "yes": "ph ph-check"},
                    "icons_stylesheet": {"href": "/static/phosphor.css"},
                }
            }
        )
    )
    assert swl.icons["close"] == "ph-light ph-x"
    assert swl.js_icons["yes"] == "ph ph-check"
    assert swl.js_icons["no"] == "bi bi-x-lg", "not given: Bootstrap's"
    hrefs = [style["href"] for style in swl.styles]
    assert "/static/phosphor.css" in hrefs
    assert not any("bootstrap-icons" in href for href in hrefs)
    modal = swl.template("swl/modal-content.j2").render()
    assert 'class="ph-light ph-x swl-icon"' in modal
    dialog = swl.template("swl/dialog.j2").render()
    assert 'class="ph ph-check swl-icon"' in dialog
    assert 'class="bi bi-x-lg swl-icon"' in dialog


def test_icons_stylesheet_left_out():
    swl = SWL(config=Config({"ui": {"icons_stylesheet": False}}))
    assert not any("bootstrap-icons" in style["href"] for style in swl.styles)


def test_icons_unknown_name():
    with pytest.raises(ValueError, match="Unknown icon names"):
        SWL(config=Config({"ui": {"icons": {"clsoe": "x"}}}))
