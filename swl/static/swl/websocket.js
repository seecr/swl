/* begin license *
 *
 * "SWL"(Seecr Web Lib) makes developing webbased apps easier
 *
 * Copyright (C) 2025-2026 Seecr (Seek You Too B.V.) https://seecr.nl
 *
 * This file is part of "Seecr Web Lib"
 *
 * "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
 * SPDX-License-Identifier: MIT
 *
 * end license */

/*
 * Live updates: the server (swl.dispatcher.Dispatcher) sends {"response": "change", "obj": <qid>}
 * when an object changed. Every element with that qid in its data-swl-on-changed attribute
 * (space separated) is rehydrated.
 *
 * The connection is restored when it drops. Changes signalled while it was down never reach
 * this page, so after a reconnect every element with data-swl-on-changed is rehydrated.
 *
 * A connection can also die without closing (a phone that slept, a network switch): when the
 * server does not answer a ping within PONG_TIMEOUT, the page reconnects. When the page
 * becomes visible again or the browser comes back online, it pings at once.
 */

const PING_INTERVAL = 10000;
const PONG_TIMEOUT = 5000;
const MAX_RECONNECT_DELAY = 30000;

function _url() {
    let protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws`;
}

function _refresh(elem) {
    htmx.trigger(elem, "swl-refresh", {context: {}}, false);
}

function _on_changed(qid) {
    for (let elem of document.querySelectorAll("[data-swl-on-changed]")) {
        if (elem.dataset.swlOnChanged.split(/\s+/).includes(qid)) {
            _refresh(elem);
        }
    }
}

export function refresh_all() {
    for (let elem of document.querySelectorAll("[data-swl-on-changed]")) {
        _refresh(elem);
    }
}

let current = null;

function connect(reconnect_delay = 1000, reconnecting = false) {
    const socket = new WebSocket(_url());
    let ping = null;
    let pong_timeout = null;
    let closed = false;

    function send_ping() {
        clearTimeout(ping);
        clearTimeout(pong_timeout);
        if (socket.readyState !== WebSocket.OPEN) {
            return;
        }
        socket.send('{"command": "ping"}');
        pong_timeout = setTimeout(reconnect, PONG_TIMEOUT);
    }

    function reconnect() {
        // from onclose, or a ping that got no answer (the socket may never close then)
        if (closed) {
            return;
        }
        closed = true;
        clearTimeout(ping);
        clearTimeout(pong_timeout);
        current = null;
        try { socket.close(); } catch (e) { /* already closed */ }
        setTimeout(
            () => connect(Math.min(reconnect_delay * 2, MAX_RECONNECT_DELAY), true),
            reconnect_delay,
        );
    }

    socket.onopen = () => {
        reconnect_delay = 1000;
        if (reconnecting) {
            refresh_all();
        }
        reconnecting = false;
    };

    socket.onmessage = (event) => {
        let response = JSON.parse(event.data);
        switch (response["response"]) {
            case "pong":
                clearTimeout(pong_timeout);
                ping = setTimeout(send_ping, PING_INTERVAL);
                break;
            case "change":
                _on_changed(response["obj"]);
                break;
            default:
                console.warn("SWL websocket: unknown message", response);
        }
    };

    socket.onclose = reconnect;

    current = {ping_now: send_ping};
}

function ping_now() {
    if (current !== null) {
        current.ping_now();
    }
}

document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
        ping_now();
    }
});
window.addEventListener("online", ping_now);

connect();
