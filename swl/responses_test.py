## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2025 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

import json
import re

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from .responses import MODAL_CONTENT, FailResponse, SuccessResponse, id_selector

from .swl import SWL
from seecr_stdlib.config import Config


def render(response):
    """(status_code, events, partials, headers) of a response, as htmx would see it."""
    status_code, headers, body = response._render()
    events = json.loads(headers.pop("HX-Trigger", "{}"))
    partials = dict(
        re.findall(
            r'<hx-partial hx-target="#([^"]+)" hx-swap="innerHTML">(.*?)</hx-partial>',
            body,
            re.S,
        )
    )
    assert body == "".join(
        f'<hx-partial hx-target="#{k}" hx-swap="innerHTML">{v}</hx-partial>'
        for k, v in partials.items()
    )
    return status_code, events, partials, headers


def test_success():
    assert render(SuccessResponse()) == (204, {}, {}, {})


def test_hydrate():
    r = SuccessResponse().hydrate("placeholder", data="content for <b>placeholder</b>")
    assert render(r) == (200, {}, {"placeholder": "content for <b>placeholder</b>"}, {})

    r = (
        SuccessResponse()
        .hydrate("one", data="1")
        .hydrate("two", data="2")
        .hydrate("one", data="1b")
    )
    assert render(r)[2] == {"two": "2", "one": "1b"}


def test_hydrate_with_rehydrate():
    with pytest.raises(ValueError) as e:
        SuccessResponse().hydrate(
            "placeholder",
            data="content for placeholder",
            rehydrate=dict(blah="something"),
        )
    assert str(e.value) == "action missing from rehydrate"

    r = SuccessResponse().hydrate(
        "placeholder",
        data="content for placeholder",
        rehydrate=dict(action="/the_action"),
    )
    assert render(r) == (
        200,
        {
            "swl-recipe": {
                "recipes": {"placeholder": {"action": "/the_action", "context": {}}}
            }
        },
        {"placeholder": "content for placeholder"},
        {},
    )


def test_hydrate_target_is_escaped():
    assert id_selector("users_list-1") == "#users_list-1"
    assert id_selector("a.b") == "#a\\2e b"
    assert id_selector("1st") == "#\\31 st"
    status_code, headers, body = SuccessResponse().hydrate('x"y', "data")._render()
    assert 'hx-target="#x\\22 y"' in body


def test_rehydrate():
    r = SuccessResponse().rehydrate("placeholder")
    assert render(r) == (
        204,
        {"swl-rehydrate": {"placeholders": {"placeholder": {}}}},
        {},
        {},
    )

    r = SuccessResponse().rehydrate("placeholder", context={"the": "value"})
    assert render(r)[1] == {
        "swl-rehydrate": {"placeholders": {"placeholder": {"the": "value"}}}
    }

    r = SuccessResponse().rehydrate("placeholder").rehydrate("placeholder2")
    r2 = SuccessResponse().rehydrate("placeholder", "placeholder2")
    assert render(r) == render(r2)
    assert render(r)[1] == {
        "swl-rehydrate": {"placeholders": {"placeholder": {}, "placeholder2": {}}}
    }

    with pytest.raises(ValueError):
        SuccessResponse().rehydrate("placeholder", {"con": "text"})


def test_call():
    r = SuccessResponse().call("some_function")
    assert render(r)[1] == {
        "swl-call": {"calls": [{"method": "some_function", "kwargs": {}}]}
    }

    r = SuccessResponse().call("call_1").call("call_2", a=1, b="two")
    assert render(r)[1] == {
        "swl-call": {
            "calls": [
                {"method": "call_1", "kwargs": {}},
                {"method": "call_2", "kwargs": {"a": 1, "b": "two"}},
            ]
        }
    }


def test_trigger():
    r = SuccessResponse().trigger("chart-changed", series="sales").call("f")
    assert render(r)[1] == {
        "chart-changed": {"series": "sales"},
        "swl-call": {"calls": [{"method": "f", "kwargs": {}}]},
    }
    with pytest.raises(ValueError):
        SuccessResponse().trigger("a").trigger("a")


def test_events_keep_their_order():
    r = SuccessResponse().close_modal().reset_form().call("f").rehydrate("p")
    assert list(render(r)[1]) == [
        "swl-modal-close",
        "swl-reset-form",
        "swl-call",
        "swl-rehydrate",
    ]


def test_session_store():
    r = SuccessResponse().session_store("key1", "value1").session_store("key2", {"a": 2})
    assert render(r)[1] == {
        "swl-session-store": {"values": {"key1": "value1", "key2": {"a": 2}}}
    }


def test_reset_form():
    assert render(SuccessResponse().reset_form())[1] == {"swl-reset-form": {}}


def test_open_modal():
    r = SuccessResponse().open_modal(data="blah")
    assert render(r) == (
        200,
        {"swl-modal-open": {"size": "lg", "scrollable": False, "calls": []}},
        {MODAL_CONTENT: "blah"},
        {},
    )

    r = SuccessResponse().open_modal(
        data="blah", call="method", size="xl", scrollable=True
    )
    assert render(r)[1] == {
        "swl-modal-open": {"size": "xl", "scrollable": True, "calls": ["method"]}
    }

    r = SuccessResponse().open_modal(
        data="blah", call=["method1", "method2"], size="huge"
    )
    assert render(r)[1] == {
        "swl-modal-open": {
            "size": "lg",
            "scrollable": False,
            "calls": ["method1", "method2"],
        }
    }

    r = SuccessResponse().open_modal(data="blah", rehydrate=dict(action="/a"))
    assert render(r)[1]["swl-recipe"] == {
        "recipes": {MODAL_CONTENT: {"action": "/a", "context": {}}}
    }

    with pytest.raises(ValueError):
        SuccessResponse().open_modal(data="blah", rehydrate=dict(context={}))


def test_hydrate_modal():
    r = SuccessResponse().hydrate_modal("modal data")
    assert render(r) == (200, {}, {MODAL_CONTENT: "modal data"}, {})

    r = SuccessResponse().hydrate_modal("modal data", call="init_modal")
    assert render(r)[1] == {"swl-modal-call": {"calls": ["init_modal"]}}

    r = SuccessResponse().hydrate_modal("modal data", call=["one", "two"])
    assert render(r)[1] == {"swl-modal-call": {"calls": ["one", "two"]}}


def test_close_modal():
    assert render(SuccessResponse().close_modal()) == (
        204,
        {"swl-modal-close": {}},
        {},
        {},
    )


def test_open_contextmenu():
    r = SuccessResponse().open_contextmenu("<ul></ul>", location={"x": 10, "y": 20})
    assert render(r) == (
        200,
        {"swl-contextmenu": {"x": 10, "y": 20}},
        {"swl-contextmenu": "<ul></ul>"},
        {},
    )


def test_redirect():
    assert render(SuccessResponse().redirect("/")) == (204, {}, {}, {"HX-Redirect": "/"})


def test_fail_response():
    assert render(FailResponse()) == (422, {"swl-error": {}}, {}, {"HX-Reswap": "none"})
    assert render(FailResponse().message("Uh Oh!")) == (
        422,
        {"swl-error": {"message": "Uh Oh!"}},
        {},
        {"HX-Reswap": "none"},
    )


def test_set_url():
    assert render(SuccessResponse().set_url("/go_here"))[3] == {
        "HX-Replace-Url": "/go_here"
    }
    r = SuccessResponse().set_url("/go_here", qid="Object:ID")
    assert render(r)[3] == {"HX-Replace-Url": "/go_here?qid=Object%3AID"}


def test_toast():
    r = SuccessResponse().toast("Changes saved.")
    assert render(r) == (
        200,
        {"swl-toast": {"delay": 500}},
        {"toast-body": "Changes saved."},
        {},
    )

    r = SuccessResponse().toast("Changes saved.", delay=1500)
    assert render(r)[1] == {"swl-toast": {"delay": 1500}}

    r = SuccessResponse().toast("Changes saved.", background="white")
    assert render(r)[1] == {"swl-toast": {"delay": 500, "background": "white"}}


def test_toast_defaults():
    swl = SWL(config=Config({}))
    assert render(swl.success().toast("Changes saved."))[1] == {
        "swl-toast": {"delay": 500}
    }

    swl = SWL(
        config=Config({"response": {"toast": {"delay": 2000, "background": "green"}}})
    )
    assert render(swl.success().toast("Changes saved."))[1] == {
        "swl-toast": {"delay": 2000, "background": "green"}
    }


def test_http_response():
    async def action(request):
        response = SuccessResponse().hydrate("p", "<i>ü</i>").call("f", name="Müller")
        response.set_cookie("c", "v")
        return response

    async def empty(request):
        return SuccessResponse().reset_form()

    async def fail(request):
        return FailResponse().message("No")

    client = TestClient(
        Starlette(routes=[Route("/a", action), Route("/e", empty), Route("/f", fail)])
    )

    response = client.get("/a")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.text == (
        '<hx-partial hx-target="#p" hx-swap="innerHTML"><i>ü</i></hx-partial>'
    )
    assert response.headers["HX-Trigger"].isascii()
    assert json.loads(response.headers["HX-Trigger"]) == {
        "swl-call": {"calls": [{"method": "f", "kwargs": {"name": "Müller"}}]}
    }
    assert response.cookies["c"] == "v"

    response = client.get("/e")
    assert response.status_code == 204
    assert response.content == b""
    assert "content-type" not in response.headers
    assert json.loads(response.headers["HX-Trigger"]) == {"swl-reset-form": {}}

    response = client.get("/f")
    assert response.status_code == 422
    assert response.headers["HX-Reswap"] == "none"
    assert json.loads(response.headers["HX-Trigger"]) == {"swl-error": {"message": "No"}}
