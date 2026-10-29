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

from .swl import SWL

from seecr_stdlib.config import Config


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


def test_swl_default():
    swl = SWL(config=Config({}))
    assert len(swl.styles) == 2
    # assert swl.web_resources.base_url == ""


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

    html = template.render(kickstart={"action": "/action/abc", "kwargs": {"qid": "Order:1"}})
    assert 'swl.kickstart("/action/abc", {"qid": "Order:1"})' in html

    # values from a url end up here: they must not be able to break out of the script
    html = template.render(kickstart={"action": "/action/abc", "kwargs": {"q": "</script><script>alert(1)"}})
    assert "</script><script>" not in html
    assert "\\u003c/script\\u003e" in html

    html = template.render(kickstart={"action": "/action/abc", "kwargs": '{"qid": "Order:1"}'})
    assert 'swl.kickstart("/action/abc", "{\\"qid\\": \\"Order:1\\"}")' in html
