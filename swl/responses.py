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

"""
Responses for SWL actions, interpreted by htmx (4.x) and swl.js.

A response consists of:
- an HTML body with one <hx-partial> per hydrated placeholder; htmx swaps each into its target;
- an HX-Trigger header with SWL events (swl-call, swl-rehydrate, swl-modal-open, ...) that swl.js
  handles after the content has been swapped, in the order the methods were called;
- HX-Redirect / HX-Replace-Url headers for redirect() and set_url().

A response without content is sent as "204 No Content", so htmx leaves the page as it is.
"""

import json
import re
from urllib.parse import urlencode

from markupsafe import escape
from starlette.responses import Response
from seecr_stdlib.config import Config

__all__ = ["SuccessResponse", "FailResponse", "MODAL_CONTENT", "CONTEXTMENU", "TOAST_BODY"]

MODAL_CONTENT = "modal-content"
CONTEXTMENU = "swl-contextmenu"
TOAST_BODY = "toast-body"

_SAFE_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def id_selector(element_id):
    """CSS selector for an element id, escaping characters that have a meaning in selectors."""
    if _SAFE_ID.match(element_id):
        return "#" + element_id
    escaped = "".join(
        ch if re.match(r"[A-Za-z0-9_-]", ch) and not (i == 0 and ch.isdigit()) else f"\\{ord(ch):x} "
        for i, ch in enumerate(element_id)
    )
    return "#" + escaped


def _check_rehydrate(rehydrate):
    if rehydrate is not None:
        if "action" not in rehydrate:
            raise ValueError("action missing from rehydrate")
        if "context" not in rehydrate:
            rehydrate["context"] = {}
    return rehydrate


class _SWLResponse(Response):
    media_type = "text/html"
    STATUS = 200

    def __init__(self, config=None):
        super().__init__(content=b"", status_code=self.STATUS)
        self._config = Config(config or {})
        self._partials = {}  # placeholder -> html, in order of hydrate()
        self._events = {}  # event name -> detail, in order of first use
        self._hx_headers = {}

    def _event(self, name, default):
        return self._events.setdefault(name, default)

    def _render(self):
        """Returns (status_code, extra_headers, body)."""
        body = "".join(
            f'<hx-partial hx-target="{escape(id_selector(placeholder))}" hx-swap="innerHTML">{data}</hx-partial>'
            for placeholder, data in self._partials.items()
        )
        headers = dict(self._hx_headers)
        if self._events:
            headers["HX-Trigger"] = json.dumps(self._events, separators=(",", ":"))
        status_code = self.STATUS
        if status_code == 200 and not body:
            status_code = 204
        return status_code, headers, body

    async def __call__(self, scope, receive, send):
        status_code, headers, body = self._render()
        # keep headers set on the response by the application (e.g. cookies)
        kept = [(k, v) for k, v in self.raw_headers if k not in (b"content-length", b"content-type")]
        self.status_code = status_code
        self.body = body.encode(self.charset) if status_code != 204 else b""
        self.init_headers()
        if status_code == 204:
            self.raw_headers = [(k, v) for k, v in self.raw_headers if k != b"content-type"]
        self.raw_headers.extend(kept)
        for key, value in headers.items():
            self.headers[key] = value
        await super().__call__(scope, receive, send)


class FailResponse(_SWLResponse):
    """The action failed; swl.js shows the message in the error dialog."""

    STATUS = 422

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hx_headers["HX-Reswap"] = "none"
        self._event("swl-error", {})

    def message(self, text):
        self._events["swl-error"]["message"] = text
        return self


class SuccessResponse(_SWLResponse):
    def hydrate(self, placeholder, data, rehydrate=None):
        """Replace the content of the element with id `placeholder` by `data` (HTML).

        With rehydrate=dict(action=..., context=...) the element is (re)configured to reload itself
        from that action, with that context, whenever it is rehydrated."""
        rehydrate = _check_rehydrate(rehydrate)
        self._partials.pop(placeholder, None)
        self._partials[placeholder] = data
        if rehydrate is not None:
            self._event("swl-recipe", {"recipes": {}})["recipes"][placeholder] = rehydrate
        return self

    def hydrate_modal(self, data, rehydrate=None, call=None):
        self.hydrate(MODAL_CONTENT, data, rehydrate=rehydrate)
        if call is not None:
            calls = self._event("swl-modal-call", {"calls": []})["calls"]
            calls.extend([call] if isinstance(call, str) else call)
        return self

    def rehydrate(self, *placeholders, context=None):
        """Let the given placeholders reload themselves, optionally with extra context."""
        context = context or {}
        targets = self._event("swl-rehydrate", {"placeholders": {}})["placeholders"]
        for placeholder in placeholders:
            if not isinstance(placeholder, str):
                raise ValueError("placeholder must be a string")
            targets[placeholder] = context
        return self

    def call(self, method, **kwargs):
        """Call the global javascript function `method` with kwargs as its only argument."""
        self._event("swl-call", {"calls": []})["calls"].append({"method": method, "kwargs": kwargs})
        return self

    def trigger(self, event, **detail):
        """Trigger a javascript event on the element that made the request (bubbles to document)."""
        if event in self._events:
            raise ValueError(f"event {event!r} already triggered in this response")
        self._events[event] = detail
        return self

    def session_store(self, key, value):
        self._event("swl-session-store", {"values": {}})["values"][key] = value
        return self

    def reset_form(self):
        self._event("swl-reset-form", {})
        return self

    def close_modal(self):
        self._event("swl-modal-close", {})
        return self

    def open_modal(self, data, size="lg", scrollable=False, call=None, rehydrate=None):
        if isinstance(call, str):
            call = [call]
        if size not in ["sm", "lg", "xl"]:
            size = "lg"
        self.hydrate(MODAL_CONTENT, data, rehydrate=rehydrate)
        self._events["swl-modal-open"] = {"size": size, "scrollable": scrollable, "calls": call or []}
        return self

    def open_contextmenu(self, data, location):
        self.hydrate(CONTEXTMENU, data)
        self._events["swl-contextmenu"] = {"x": location["x"], "y": location["y"]}
        return self

    def redirect(self, url):
        self._hx_headers["HX-Redirect"] = url
        return self

    def set_url(self, url, **kwargs):
        target_url = url
        if len(kwargs) > 0:
            target_url = "{}?{}".format(url, urlencode(kwargs))
        self._hx_headers["HX-Replace-Url"] = target_url
        return self

    def toast(self, text, delay=None, background=None):
        if delay is None:
            delay = self._config.get("toast.delay", 500)
        toast_options = {"delay": delay}

        if background is None:
            background = self._config.get("toast.background")
        if background is not None:
            toast_options["background"] = background

        self.hydrate(TOAST_BODY, text)
        self._events["swl-toast"] = toast_options
        return self
