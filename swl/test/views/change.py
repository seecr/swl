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


async def swl_change_select(request, **kwargs):
    async with request.form() as form:
        value = form["select"]

        return SuccessResponse().hydrate("the_place", data=value)


__actions__ = [
    dict(authenticated=False, method=swl_change_select),
]
