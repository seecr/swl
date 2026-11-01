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

"""Live updates: tell open pages that an object changed.

Every open page connects to the websocket (`endpoint`). `signal_change(obj)` sends the qid
of `obj` to the pages; websocket.js reloads the placeholders that listen to that qid.

The qid goes to every open page, unless `users` is given: then only the pages of those
users get it, so the qid (and what it says, e.g. who talks to whom) stays private. A page
belongs to the user that is logged in when it connects: `websocket.user.identity`
(Starlette's `BaseUser.identity`), which needs the `AuthenticationMiddleware`.

With `Dispatcher(authenticated=True)` only logged-in users can connect.
"""

from starlette.websockets import WebSocketDisconnect

POLICY_VIOLATION = 1008  # websocket close code: not allowed


def user_identity(websocket):
    """The identity of the logged-in user of this websocket, or None."""
    if "user" not in websocket.scope:
        return None
    user = websocket.user
    if not user.is_authenticated:
        return None
    return user.identity


class Dispatcher:
    def __init__(self, authenticated=False, identify=user_identity):
        self._authenticated = authenticated
        self._identify = identify
        self._listeners = {}  # websocket -> identity of its user (or None)

    async def _pong(self, websocket):
        await websocket.send_json({"response": "pong"})

    async def endpoint(self, websocket):
        identity = self._identify(websocket)
        if self._authenticated and identity is None:
            await websocket.close(code=POLICY_VIOLATION)
            return
        await websocket.accept()
        await self._pong(websocket)
        self._listeners[websocket] = identity
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    break
                await self.handle(websocket, data)
        finally:
            self._listeners.pop(websocket, None)

    def connected_users(self):
        """The identities of the users with at least one open page."""
        return {identity for identity in self._listeners.values() if identity is not None}

    async def signal_change(self, obj, users=None):
        """Send the qid of `obj` (an object with a `qid`, or the qid itself) to the open
        pages; with `users` (identities) only to the pages of those users."""
        qid = obj if isinstance(obj, str) else obj.qid
        if users is not None:
            users = {users} if isinstance(users, str) else set(users)
        # a copy: closed sockets are removed below
        for websocket, identity in list(self._listeners.items()):
            if users is not None and identity not in users:
                continue
            try:
                await websocket.send_json({"response": "change", "obj": qid})
            except Exception:
                self._listeners.pop(websocket, None)

    async def handle(self, websocket, data):
        if data.get("command") == "ping":
            await self._pong(websocket)
            return
