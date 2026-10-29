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
 * (space separated) is rehydrated. The connection is restored when it drops.
 */

const PING_INTERVAL = 10000;
const MAX_RECONNECT_DELAY = 30000;

function _url() {
    let protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws`;
}

function _on_changed(qid) {
    for (let elem of document.querySelectorAll("[data-swl-on-changed]")) {
        if (elem.dataset.swlOnChanged.split(/\s+/).includes(qid)) {
            htmx.trigger(elem, "swl-refresh", {context: {}}, false);
        }
    }
}

function connect(reconnect_delay = 1000) {
    const socket = new WebSocket(_url());
    let ping = null;

    socket.onopen = () => { reconnect_delay = 1000; };

    socket.onmessage = (event) => {
        let response = JSON.parse(event.data);
        switch (response["response"]) {
            case "pong":
                ping = setTimeout(() => socket.send('{"command": "ping"}'), PING_INTERVAL);
                break;
            case "change":
                _on_changed(response["obj"]);
                break;
            default:
                console.warn("SWL websocket: unknown message", response);
        }
    };

    socket.onclose = () => {
        clearTimeout(ping);
        setTimeout(() => connect(Math.min(reconnect_delay * 2, MAX_RECONNECT_DELAY)), reconnect_delay);
    };
}

connect();
