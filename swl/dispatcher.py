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

from starlette.websockets import WebSocketDisconnect


class Dispatcher:
    def __init__(self):
        self._listeners = []

    async def _pong(self, websocket):
        await websocket.send_json({"response": "pong"})

    async def endpoint(self, websocket):
        await websocket.accept()
        await self._pong(websocket)
        self._listeners.append(websocket)
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                self._listeners.remove(websocket)
                break
            await self.handle(websocket, data)

    async def signal_change(self, obj):
        # a copy: closed sockets are removed below
        for websocket in list(self._listeners):
            try:
                await websocket.send_json({"response": "change", "obj": obj.qid})
            except Exception:
                self._listeners.remove(websocket)

    async def handle(self, websocket, data):
        if data["command"] == "ping":
            await self._pong(websocket)
            return
