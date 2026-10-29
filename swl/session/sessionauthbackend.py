## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024, 2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

from starlette.authentication import AuthCredentials, AuthenticationBackend

__all__ = ["SessionAuthBackend"]


class SessionAuthBackend(AuthenticationBackend):
    def __init__(self, userbase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._userbase = userbase

    async def authenticate(self, conn):
        if (username := conn.session.get("username")) is not None:
            user = self._userbase.get(username)
            return AuthCredentials(["authenticated"]), user


# TODO ["authenticated"] should add "admin" if user.admin
