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


async def swl_open_modal(request, **kwargs):
    async with request.form() as form:
        return SuccessResponse().open_modal(
            data="This is the modal",
            size=form.get("size", "lg"),
            call=form.get("call"),
        )


async def swl_hydrate_modal_call(request, **kwargs):
    return SuccessResponse().hydrate_modal("Replaced content", call="swl_test_record")


async def swl_close_modal(request, **kwargs):
    return SuccessResponse().close_modal()


__actions__ = [
    dict(authenticated=False, method=swl_open_modal),
    dict(authenticated=False, method=swl_close_modal),
    dict(authenticated=False, method=swl_hydrate_modal_call),
]
