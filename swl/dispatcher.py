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

Who is online: `connected_users()`. A subclass can react when a user's first page
connects (`user_connected`) and when their last page closes (`user_disconnected`).
websocket.js pings every 10 seconds; with `idle_timeout` (seconds) a page that has not
sent anything for that long is closed (a phone that went to sleep, a lost network), so it
does not count as online forever. Background tabs ping less often (browsers slow down
their timers, to once a minute), so keep it well above a minute.
"""

import asyncio
import logging

from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

POLICY_VIOLATION = 1008  # websocket close code: not allowed
GOING_AWAY = 1001  # websocket close code: the server closes an idle connection


def user_identity(websocket):
    """The identity of the logged-in user of this websocket, or None."""
    if "user" not in websocket.scope:
        return None
    user = websocket.user
    if not user.is_authenticated:
        return None
    return user.identity


class Dispatcher:
    def __init__(self, authenticated=False, identify=user_identity, idle_timeout=None):
        self._authenticated = authenticated
        self._identify = identify
        self._idle_timeout = idle_timeout
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
        first = identity is not None and identity not in self.connected_users()
        self._listeners[websocket] = identity
        if first:
            await self._call_hook(self.user_connected, identity)
        try:
            while True:
                try:
                    data = await self._receive(websocket)
                except WebSocketDisconnect:
                    break
                except asyncio.TimeoutError:
                    await self._close(websocket, GOING_AWAY)
                    break
                await self.handle(websocket, data)
        finally:
            self._listeners.pop(websocket, None)
            if identity is not None and identity not in self.connected_users():
                await self._call_hook(self.user_disconnected, identity)

    async def _receive(self, websocket):
        if self._idle_timeout is None:
            return await websocket.receive_json()
        return await asyncio.wait_for(websocket.receive_json(), self._idle_timeout)

    @staticmethod
    async def _close(websocket, code):
        try:
            await websocket.close(code=code)
        except Exception:
            pass  # already gone

    @staticmethod
    async def _call_hook(hook, identity):
        try:
            await hook(identity)
        except Exception:
            logger.exception(f"{hook.__name__}({identity!r}) failed")

    async def user_connected(self, identity):
        """The first open page of this user connected. For subclasses."""

    async def user_disconnected(self, identity):
        """The last open page of this user closed. For subclasses."""

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
