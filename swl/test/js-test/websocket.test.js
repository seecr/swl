/* begin license *
 *
 * "SWL"(Seecr Web Lib) makes developing webbased apps easier
 *
 * Copyright (C) 2026 Seecr (Seek You Too B.V.) https://seecr.nl
 *
 * This file is part of "Seecr Web Lib"
 *
 * "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
 * SPDX-License-Identifier: MIT
 *
 * end license */

/*
 * Tests for websocket.js (live updates) with a fake WebSocket: no server needed.
 */

class FakeWebSocket {
    static OPEN = 1;
    static instances = [];

    constructor(url) {
        this.url = url;
        this.readyState = 0;
        this.sent = [];
        FakeWebSocket.instances.push(this);
    }

    send(data) { this.sent.push(JSON.parse(data)); }

    close() {
        if (this.readyState === 3) { return; }
        this.readyState = 3;
        this.onclose?.({});
    }

    // what the server does
    open() { this.readyState = FakeWebSocket.OPEN; this.onopen?.({}); }
    receive(message) { this.onmessage?.({data: JSON.stringify(message)}); }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const last_socket = () => FakeWebSocket.instances[FakeWebSocket.instances.length - 1];

function waitFor(condition, what, timeout = 8000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        (function poll() {
            if (condition()) { return resolve(); }
            if (Date.now() - start > timeout) { return reject(new Error(`timeout: ${what}`)); }
            setTimeout(poll, 20);
        })();
    });
}

QUnit.module("websocket.js", (hooks) => {
    let refreshed = [];
    let elem;

    hooks.before(async () => {
        window.WebSocket = FakeWebSocket;
        await import("/static/swl/websocket.js?fake");
        last_socket().open();
        last_socket().receive({response: "pong"});
    });

    hooks.beforeEach(() => {
        refreshed = [];
        elem = document.createElement("div");
        elem.innerHTML = `
            <div id="ws-a" data-swl-on-changed="Room:1 rooms"></div>
            <div id="ws-b" data-swl-on-changed="Chat:2"></div>
            <div id="ws-c"></div>`;
        document.body.appendChild(elem);
        for (let id of ["ws-a", "ws-b", "ws-c"]) {
            document.getElementById(id).addEventListener("swl-refresh", () => refreshed.push(id));
        }
    });

    hooks.afterEach(() => elem.remove());

    QUnit.test("a change rehydrates the elements that listen to its qid", async (assert) => {
        last_socket().receive({response: "change", obj: "rooms"});
        last_socket().receive({response: "change", obj: "Chat:2"});
        last_socket().receive({response: "change", obj: "Chat:3"});
        await sleep(20);
        assert.deepEqual(refreshed, ["ws-a", "ws-b"]);
    });

    QUnit.test("after a reconnect every listening element is rehydrated", async (assert) => {
        let before = FakeWebSocket.instances.length;
        last_socket().close();
        await waitFor(() => FakeWebSocket.instances.length === before + 1, "reconnect");
        assert.deepEqual(refreshed, [], "nothing yet: the new socket is not open");
        last_socket().open();
        await sleep(20);
        assert.deepEqual(refreshed.sort(), ["ws-a", "ws-b"], "all, once the socket is open");
        last_socket().receive({response: "pong"});
    });

    QUnit.test("no answer to a ping: reconnect and rehydrate", async (assert) => {
        let socket = last_socket();
        socket.sent = [];
        window.dispatchEvent(new Event("online"));
        assert.deepEqual(socket.sent, [{command: "ping"}], "coming online pings at once");
        // the server does not answer: after PONG_TIMEOUT (5 s) and the reconnect delay
        await waitFor(() => last_socket() !== socket, "reconnect");
        assert.equal(socket.readyState, 3, "the dead socket is closed");
        last_socket().open();
        await sleep(20);
        assert.deepEqual(refreshed.sort(), ["ws-a", "ws-b"]);
        last_socket().receive({response: "pong"});
    });

    QUnit.test("a pong in time keeps the connection", async (assert) => {
        let socket = last_socket();
        socket.sent = [];
        window.dispatchEvent(new Event("online"));
        socket.receive({response: "pong"});
        await sleep(100);
        assert.equal(last_socket(), socket);
        assert.deepEqual(refreshed, []);
    });
});
