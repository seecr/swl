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

from types import SimpleNamespace

import pytest
from starlette.applications import Starlette
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from .dispatcher import Dispatcher


class HeaderAuth(AuthenticationBackend):
    """The user named in the x-user header; for these tests only."""

    async def authenticate(self, conn):
        if (username := conn.headers.get("x-user")) is not None:
            return AuthCredentials(["authenticated"]), SimpleUser(username)


def client_for(dispatcher, auth=True):
    middleware = [Middleware(AuthenticationMiddleware, backend=HeaderAuth())]
    app = Starlette(
        routes=[WebSocketRoute("/ws", dispatcher.endpoint)],
        middleware=middleware if auth else [],
    )
    return TestClient(app)


def connect(client, user=None):
    headers = {} if user is None else {"x-user": user}
    websocket = client.websocket_connect("/ws", headers=headers)
    return websocket


async def test_disconnect_on_error_sending():
    dispatcher = Dispatcher()

    class MockSock:
        async def send_json(*arg, **kwargs):
            raise RuntimeError("Something went wrong")

    dispatcher._listeners[MockSock()] = None
    assert len(dispatcher._listeners) == 1
    await dispatcher.signal_change(SimpleNamespace(qid="class:id"))
    assert len(dispatcher._listeners) == 0


def test_changes_go_to_every_page_without_users():
    dispatcher = Dispatcher()
    with (
        client_for(dispatcher) as client,
        connect(client, "alice") as alice,
        connect(client) as anonymous,
    ):
        assert alice.receive_json() == {"response": "pong"}
        assert anonymous.receive_json() == {"response": "pong"}
        client.portal.call(dispatcher.signal_change, SimpleNamespace(qid="Room:1"))
        assert alice.receive_json() == {"response": "change", "obj": "Room:1"}
        assert anonymous.receive_json() == {"response": "change", "obj": "Room:1"}


def test_works_without_authentication_middleware():
    dispatcher = Dispatcher()
    with client_for(dispatcher, auth=False) as client, connect(client) as websocket:
        assert websocket.receive_json() == {"response": "pong"}
        assert dispatcher.connected_users() == set()
        client.portal.call(dispatcher.signal_change, "tasks")
        assert websocket.receive_json() == {"response": "change", "obj": "tasks"}


def test_changes_only_go_to_the_given_users():
    dispatcher = Dispatcher()
    with (
        client_for(dispatcher) as client,
        connect(client, "alice") as alice,
        connect(client, "alice") as alice_phone,
        connect(client, "bob") as bob,
        connect(client, "carol") as carol,
        connect(client) as anonymous,
    ):
        for websocket in (alice, alice_phone, bob, carol, anonymous):
            assert websocket.receive_json() == {"response": "pong"}
        assert dispatcher.connected_users() == {"alice", "bob", "carol"}

        client.portal.call(
            lambda: dispatcher.signal_change("Chat:secret", users=["alice", "bob"])
        )
        client.portal.call(lambda: dispatcher.signal_change("Chat:other", users="carol"))
        client.portal.call(dispatcher.signal_change, "rooms")

        assert alice.receive_json() == {"response": "change", "obj": "Chat:secret"}
        assert alice_phone.receive_json() == {"response": "change", "obj": "Chat:secret"}
        assert bob.receive_json() == {"response": "change", "obj": "Chat:secret"}
        # carol and the anonymous page never see Chat:secret: their next message is
        # the next change meant for them
        assert carol.receive_json() == {"response": "change", "obj": "Chat:other"}
        assert carol.receive_json() == {"response": "change", "obj": "rooms"}
        assert anonymous.receive_json() == {"response": "change", "obj": "rooms"}
        for websocket in (alice, alice_phone, bob):
            assert websocket.receive_json() == {"response": "change", "obj": "rooms"}


def test_closed_pages_are_forgotten():
    dispatcher = Dispatcher()
    with client_for(dispatcher) as client, connect(client, "alice") as alice:
        alice.receive_json()
        with connect(client, "bob") as bob:
            bob.receive_json()
            assert dispatcher.connected_users() == {"alice", "bob"}
        # the server side notices the close when it receives
        alice.send_json({"command": "ping"})
        assert alice.receive_json() == {"response": "pong"}
        assert dispatcher.connected_users() == {"alice"}


def test_authenticated_refuses_anonymous_pages():
    dispatcher = Dispatcher(authenticated=True)
    client = client_for(dispatcher)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with connect(client) as websocket:
            websocket.receive_json()
    assert exc_info.value.code == 1008
    assert dispatcher.connected_users() == set()

    with connect(client, "alice") as alice:
        assert alice.receive_json() == {"response": "pong"}
        assert dispatcher.connected_users() == {"alice"}


def test_own_identify():
    dispatcher = Dispatcher(identify=lambda websocket: websocket.headers.get("x-device"))
    client = client_for(dispatcher, auth=False)
    with client.websocket_connect("/ws", headers={"x-device": "d1"}) as websocket:
        websocket.receive_json()
        assert dispatcher.connected_users() == {"d1"}


def test_ping():
    dispatcher = Dispatcher()
    with client_for(dispatcher) as client, connect(client, "alice") as alice:
        assert alice.receive_json() == {"response": "pong"}
        alice.send_json({"command": "ping"})
        assert alice.receive_json() == {"response": "pong"}
