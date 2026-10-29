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

from starlette.applications import Starlette

from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient


from .dispatcher import Dispatcher


async def test_disconnect_on_error_sending(tmp_path):
    dispatcher = Dispatcher()

    class MockSock:
        async def send_json(*arg, **kwargs):
            pass

    class MockObj:
        def __init__(self):
            self.qid = "class:id"

    ws = MockSock()
    obj = MockObj()

    dispatcher._listeners.append(ws)

    def raise_ex(*args, **kwargs):
        raise RuntimeError("Something went wrong")

    ws.send_json = raise_ex
    assert len(dispatcher._listeners) == 1
    await dispatcher.signal_change(obj)
    assert len(dispatcher._listeners) == 0
