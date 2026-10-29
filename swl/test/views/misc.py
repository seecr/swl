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

import asyncio
import itertools

from starlette.responses import HTMLResponse

from swl.responses import FailResponse, SuccessResponse

_counter = itertools.count(1)


async def swl_echo(request, **kwargs):
    """Puts the posted fields, sorted, into 'the_place'."""
    async with request.form() as form:
        value = "&".join(f"{k}={v}" for k, v in sorted(form.multi_items()))
        return SuccessResponse().hydrate("the_place", data=value)


async def swl_html(request, **kwargs):
    return HTMLResponse("<html><body>Please log in</body></html>")


async def swl_error(request, **kwargs):
    raise RuntimeError("Intentional error for testing")


async def swl_forbidden(request, **kwargs):
    return SuccessResponse()


async def swl_fail(request, **kwargs):
    return FailResponse().message("That did not work")


async def swl_calls(request, **kwargs):
    return (
        SuccessResponse()
        .call("swl_test_does_not_exist")
        .call("swl_test_record", value="after")
    )


async def swl_reset_form(request, **kwargs):
    return SuccessResponse().reset_form()


async def swl_toast(request, **kwargs):
    return SuccessResponse().toast("Saved <b>it</b>", delay=500)


async def swl_session_store(request, **kwargs):
    return SuccessResponse().session_store("swl_test_key", {"a": [1, 2]})


async def swl_contextmenu(request, **kwargs):
    async with request.form() as form:
        x, y = int(form["event_x"]), int(form["event_y"])
        return SuccessResponse().open_contextmenu(
            f"menu for {form['item']}", location={"x": x, "y": y}
        )


async def swl_counted(request, **kwargs):
    """Hydrates the requested placeholder with a counter, and a recipe to reload it."""
    async with request.form() as form:
        placeholder = form["placeholder"]
        return SuccessResponse().hydrate(
            placeholder,
            data=f"count={next(_counter)} extra={form.get('extra', '')}",
            rehydrate=dict(
                action="/action/swl_counted", context={"placeholder": placeholder}
            ),
        )


async def swl_slow_outer(request, **kwargs):
    """A placeholder that loads slowly and contains another slow placeholder (for
    kickstart)."""
    await asyncio.sleep(0.3)
    return SuccessResponse().hydrate(
        "outer",
        data='<div id="inner" hx-post="/action/swl_slow_inner" hx-trigger="load"></div>',
    )


async def swl_slow_inner(request, **kwargs):
    await asyncio.sleep(0.2)
    return SuccessResponse().hydrate("inner", data='<div id="the_place"></div>')


async def swl_rehydrate(request, **kwargs):
    async with request.form() as form:
        context = {k: v for k, v in form.items() if k not in ("target", "placeholder")}
        return SuccessResponse().rehydrate(form["target"], context=context)


__actions__ = [
    dict(authenticated=False, method=swl_echo),
    dict(authenticated=False, method=swl_html),
    dict(authenticated=False, method=swl_error),
    dict(authenticated=True, method=swl_forbidden),
    dict(authenticated=False, method=swl_fail),
    dict(authenticated=False, method=swl_calls),
    dict(authenticated=False, method=swl_reset_form),
    dict(authenticated=False, method=swl_toast),
    dict(authenticated=False, method=swl_session_store),
    dict(authenticated=False, method=swl_contextmenu),
    dict(authenticated=False, method=swl_counted),
    dict(authenticated=False, method=swl_rehydrate),
    dict(authenticated=False, method=swl_slow_outer),
    dict(authenticated=False, method=swl_slow_inner),
]
