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

from swl.responses import SuccessResponse


async def swl_hydrate_button(request, **kwargs):
    async with request.form() as form:
        value = form["text"]

        return SuccessResponse().hydrate(
            "the_place",
            data=value,
            rehydrate=dict(
                action="/action/swl_hydrate_button", context=dict(text=value)
            ),
        )


async def swl_rehydrate_button(request, **kwargs):
    async with request.form() as form:
        value = form["text"]

        return SuccessResponse().rehydrate("the_place", context=dict(text=value))


async def swl_placeholder(request, **kwargs):
    async with request.form() as form:
        value = form["some_id"]

        return SuccessResponse().hydrate(
            "the_place",
            data=f"ID -> {value}",
            rehydrate=dict(
                action="/action/swl_placeholder", context=dict(some_id=value)
            ),
        )


__actions__ = [
    dict(authenticated=False, method=swl_hydrate_button),
    dict(authenticated=False, method=swl_rehydrate_button),
    dict(authenticated=False, method=swl_placeholder),
]
