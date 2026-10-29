/* begin license *
 *
 * "SWL"(Seecr Web Lib) makes developing webbased apps easier
 *
 * Copyright (C) 2024-2026 Seecr (Seek You Too B.V.) https://seecr.nl
 *
 * This file is part of "Seecr Web Lib"
 *
 * "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
 * SPDX-License-Identifier: MIT
 *
 * end license */

/*
 * SWL on top of htmx 4.
 *
 * htmx issues the requests (hx-post, hx-trigger, hx-vals, hx-confirm, ...) and swaps the
 * <hx-partial> elements of an SWL response into the page. This module handles the SWL events that
 * the server sends in the HX-Trigger header (see swl/responses.py) and adds:
 *  - the SWL dialog for hx-confirm and for errors,
 *  - error reporting for failed requests,
 *  - rehydrating placeholders ("swl-refresh"),
 *  - data-swl-validate, and the "placeholder" / event_x / event_y request parameters.
 *
 * Everything is set up once, on document, when this module is loaded.
 */

import { _get } from "./lang.js"

const REFRESH_EVENT = "swl-refresh";
const FORM_ELEMENTS = "button, input, select, textarea, form";

/* ---------------------------------------------------------------- utilities */

function _call_function(name, ...args) {
    let fn = window[name];
    if (typeof fn !== "function") {
        console.error("SWL: function not found: " + name);
        ui.error(_get("error_unknown_function") + ": " + name);
        return undefined;
    }
    try {
        return fn(...args);
    } catch (error) {
        console.error("SWL: error in function " + name, error);
        ui.error(_get("error_function_failed") + ": " + name);
        return undefined;
    }
}

function _as_list(value) {
    if (value === undefined || value === null) {
        return [];
    }
    return Array.isArray(value) ? value : [value];
}

function _set_values(body, values) {
    for (let [key, value] of Object.entries(values || {})) {
        body.delete(key);
        for (let each of _as_list(value)) {
            body.append(key, each);
        }
    }
}

/* Add the values of a form, a form field, or the named fields inside an element. */
function _add_fields(body, node) {
    if (node instanceof HTMLFormElement) {
        for (let [key, value] of new FormData(node)) {
            body.append(key, value);
        }
        return;
    }
    let fields = node.matches("[name]") ? [node] : node.querySelectorAll("[name]");
    for (let field of fields) {
        if (field.disabled || field.matches("button") || (["checkbox", "radio"].includes(field.type) && !field.checked)) {
            continue;
        }
        if (field.type === "select-multiple") {
            for (let option of field.selectedOptions) {
                body.append(field.name, option.value);
            }
        } else {
            body.append(field.name, field.value);
        }
    }
}

function _on(event_name, handler, capture = false) {
    document.addEventListener(event_name, handler, capture);
}

/* ---------------------------------------------------------------- dialog */

/* The SWL dialog (swl/dialog.j2): a native <dialog> for confirmations and messages. */
function _dialog() {
    return document.querySelector("dialog.swl-dialog") ?? document.querySelector(".swl-dialog");
}

function _show_dialog(icon_classes, title, message, buttons, on_escape) {
    let dialog = _dialog();
    if (!dialog) {
        console.error("SWL: dialog not found; message: " + message);
        return null;
    }
    for (let elem of dialog.querySelectorAll("[data-swl-lang-key]")) {
        elem.textContent = _get(elem.dataset.swlLangKey);
    }
    let icon = dialog.querySelector(".swl-dialog-header h5 i");
    if (icon) {
        icon.className = "bi " + icon_classes;
    }
    let title_elem = dialog.querySelector(".swl-dialog-header h5 span");
    if (title_elem && title !== null) {
        title_elem.textContent = title;
    }
    let message_elem = dialog.querySelector("#swl-dialog-msg");
    if (message_elem) {
        message_elem.textContent = message ?? "";
    }
    let close = () => dialog.close ? dialog.close() : (dialog.style.display = "none");
    for (let button of dialog.querySelectorAll("button")) {
        button.style.display = "none";
        button.onclick = null;
    }
    let first = null;
    for (let [selector, on_click] of Object.entries(buttons)) {
        let button = dialog.querySelector(selector);
        if (button) {
            button.style.display = "";
            button.onclick = () => { close(); on_click(); };
            first = first ?? button;
        }
    }
    // Escape answers like the first button (No, Ok)
    dialog.oncancel = (e) => { e.preventDefault(); close(); on_escape(); };
    if (dialog.showModal) {
        if (!dialog.open) {
            dialog.showModal();
        }
    } else {
        dialog.style.display = "block";
    }
    first?.focus();
    return dialog;
}

const ui = {
    confirm: (message) => new Promise((resolve) => {
        let shown = _show_dialog("bi-question-diamond-fill swl-icon-warning", null, message, {
            ".swl-btn-decline": () => resolve(false),
            ".swl-btn-confirm": () => resolve(true),
        }, () => resolve(false));
        if (!shown) {
            resolve(window.confirm(message));
        }
    }),
    error: (message) => _show_dialog("bi-exclamation-circle-fill swl-icon-danger", _get("error"), message, {".swl-btn-ok": () => {}}, () => {}),
    info: (message) => _show_dialog("bi-info-circle-fill swl-icon-info", _get("info"), message, {".swl-btn-ok": () => {}}, () => {}),
};

/* ---------------------------------------------------------------- modal */

/*
 * The modal (swl/modal.j2) is a native <dialog>. An application that still has its own
 * Bootstrap modal markup with id "swl-modal" (a div.modal) gets the Bootstrap modal instead.
 */
function _modal() {
    return document.getElementById("swl-modal");
}

function _is_native(modal) {
    return modal instanceof HTMLDialogElement;
}

function _modal_is_open(modal) {
    return _is_native(modal) ? modal.open : modal.classList.contains("show");
}

function _bootstrap_modal(modal) {
    return bootstrap.Modal.getOrCreateInstance(modal, {keyboard: false, backdrop: "static"});
}

/* Run methods once the modal is shown; right away when it already is. */
function _call_on_modal_shown(modal, methods) {
    methods = _as_list(methods);
    if (methods.length == 0) {
        return;
    }
    let call_all = () => methods.forEach((method_name) => _call_function(method_name));
    if (_modal_is_open(modal)) {
        call_all();
    } else {
        modal.addEventListener(_is_native(modal) ? "swl-modal-shown" : "shown.bs.modal", call_all, {once: true});
    }
}

function _open_modal(modal, size, scrollable) {
    if (!_is_native(modal)) {
        let dialog = modal.querySelector(".modal-dialog");
        dialog.classList.toggle("modal-dialog-scrollable", scrollable);
        dialog.classList.remove("modal-sm", "modal-lg", "modal-xl");
        dialog.classList.add("modal-" + size);
        _bootstrap_modal(modal).show();
        return;
    }
    modal.classList.remove("swl-modal-sm", "swl-modal-lg", "swl-modal-xl");
    modal.classList.add("swl-modal-" + size);
    modal.classList.toggle("swl-modal-scrollable", scrollable);
    if (!modal.open) {
        modal.showModal();
        modal.dispatchEvent(new CustomEvent("swl-modal-shown"));
    }
}

function _close_modal(modal) {
    if (_is_native(modal)) {
        modal.close();
    } else {
        _bootstrap_modal(modal).hide();
    }
}

/* The modal does not close on Escape (like a form you could lose by accident); use its close button. */
_on("cancel", (e) => {
    if (e.target === _modal()) {
        e.preventDefault();
    }
}, true);

/* A button with data-swl-close (or Bootstrap's data-bs-dismiss="modal") closes the <dialog> it is in. */
_on("click", (e) => {
    let button = e.target.closest?.("[data-swl-close], [data-bs-dismiss=modal]");
    let dialog = button?.closest("dialog");
    if (dialog) {
        dialog.close();
    }
});

/* ---------------------------------------------------------------- SWL response events */

_on("swl-error", (e) => ui.error(e.detail.message || _get("error_server")));

_on("swl-call", (e) => {
    for (let each of e.detail.calls || []) {
        _call_function(each.method, each.kwargs);
    }
});

/* Ask placeholders to reload; context is added to the request (see htmx:config:request below). */
_on("swl-rehydrate", (e) => {
    for (let [id, context] of Object.entries(e.detail.placeholders || {})) {
        let elem = document.getElementById(id);
        if (elem) {
            htmx.trigger(elem, REFRESH_EVENT, {context: context}, false);  // no bubbling: nested placeholders stay put
        }
    }
});

/* Store how a placeholder reloads itself: on the element, as hx-post and hx-vals. */
_on("swl-recipe", (e) => {
    for (let [id, recipe] of Object.entries(e.detail.recipes || {})) {
        let elem = document.getElementById(id);
        if (!elem) {
            continue;
        }
        elem.setAttribute("hx-post", recipe.action);
        elem.setAttribute("hx-vals", JSON.stringify(recipe.context || {}));
        if (!elem.hasAttribute("hx-trigger")) {
            elem.setAttribute("hx-trigger", REFRESH_EVENT);
        }
        htmx.process(elem);
    }
});

_on("swl-reset-form", (e) => {
    let form = e.target.form || e.target.closest?.("form");
    form?.reset();
});

_on("swl-session-store", (e) => {
    for (let [key, value] of Object.entries(e.detail.values || {})) {
        window.sessionStorage.setItem(key, JSON.stringify(value));
    }
});

_on("swl-modal-open", (e) => {
    let modal = _modal();
    if (!modal) {
        ui.error("Modal dialog not found.");
        return;
    }
    _open_modal(modal, e.detail.size || "lg", e.detail.scrollable == true);
    _call_on_modal_shown(modal, e.detail.calls);
});

_on("swl-modal-call", (e) => {
    let modal = _modal();
    if (modal) {
        _call_on_modal_shown(modal, e.detail.calls);
    }
});

_on("swl-modal-close", () => {
    let modal = _modal();
    if (modal) {
        _close_modal(modal);
    }
});

/* The context menu (swl/contextmenu.j2) is a popover: a click outside it or Escape closes it. */
_on("swl-contextmenu", (e) => {
    let menu = document.getElementById("swl-contextmenu");
    if (!menu) {
        ui.error("Context dialog not found.");
        return;
    }
    // x and y are page coordinates; the popover is positioned in the viewport
    let left = e.detail.x - window.scrollX - 8;
    let top = e.detail.y - window.scrollY - 8;
    if (menu.matches(":popover-open")) {
        menu.hidePopover();
    }
    Object.assign(menu.style, {left: left + "px", top: top + "px"});
    menu.showPopover();
    // keep it inside the window
    let rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        menu.style.left = Math.max(0, window.innerWidth - rect.width - 4) + "px";
    }
    if (rect.bottom > window.innerHeight) {
        menu.style.top = Math.max(0, window.innerHeight - rect.height - 4) + "px";
    }
    let hide = () => { if (menu.matches(":popover-open")) menu.hidePopover(); };
    menu.onmouseleave = hide;
    menu.onclick = (click) => { if (click.target.closest("button, a")) hide(); };
});

/* The toast (swl/toast.j2) is a popover that hides itself after `delay` ms. */
let _toast_timer = null;
_on("swl-toast", (e) => {
    let elem = document.getElementById("toast");
    if (!elem) {
        return;
    }
    elem.removeAttribute("style");
    if (e.detail.background) {
        elem.style.backgroundColor = e.detail.background;
        elem.style.backdropFilter = "none";
    }
    clearTimeout(_toast_timer);
    if (elem.matches(":popover-open")) {
        elem.hidePopover();  // and show again: on top of a modal that opened in the meantime
    }
    elem.showPopover();
    _toast_timer = setTimeout(() => {
        if (elem.matches(":popover-open")) {
            elem.hidePopover();
        }
    }, (e.detail.delay ?? 500) + 200);  // + the time it takes to fade in
});

/* ---------------------------------------------------------------- htmx integration */

/* Extra request parameters, data-swl-validate */
_on("htmx:config:request", (e) => {
    let ctx = e.detail.ctx;
    let elem = ctx.sourceElement;
    let body = ctx.request.body;
    let source_event = ctx.sourceEvent;

    let validate = elem.getAttribute?.("data-swl-validate");
    if (validate && !_call_function(validate)) {
        e.preventDefault();  // cancels the request
        return;
    }
    if (!(body instanceof FormData)) {
        return;
    }
    if (!elem.matches?.(FORM_ELEMENTS)) {
        // htmx would post every named field inside the element (or its enclosing form). A placeholder,
        // link or swl_action call only sends its own values and the fields named in its hx-include.
        body = new FormData();
        let include = elem.getAttribute?.("hx-include");
        if (include) {
            for (let node of htmx.findAll(elem, include)) {
                _add_fields(body, node);
            }
        }
        _set_values(body, ctx.vals);
        _set_values(body, ctx.values);
        ctx.request.body = body;
    }
    if (elem.id && !body.has("placeholder")) {
        body.set("placeholder", elem.id);
    }
    if (source_event?.type === REFRESH_EVENT) {
        _set_values(body, source_event.detail?.context);
    }
    if (source_event?.type === "contextmenu") {
        body.set("event_x", source_event.pageX);
        body.set("event_y", source_event.pageY);
    }
});

/* hx-confirm uses the SWL dialog (hx-confirm="js:..." is left to htmx) */
_on("htmx:confirm", (e) => {
    let question = e.detail.ctx.confirm;
    if (question.startsWith("js:") || question.startsWith("javascript:")) {
        return;
    }
    e.preventDefault();
    ui.confirm(question).then((ok) => ok ? e.detail.issueRequest() : e.detail.dropRequest());
});

/* A request that was redirected (e.g. to the login page after the session expired) becomes a page load. */
_on("htmx:before:response", (e) => {
    let raw = e.detail.ctx.response.raw;
    if (raw.redirected) {
        e.preventDefault();
        window.location.href = raw.url;
    }
});

function _message_for_status(status) {
    let message;
    if (status === 401 || status === 403) {
        message = _get("error_forbidden");
    } else if (status === 404) {
        message = _get("error_not_found");
    } else {
        message = _get("error_server");
    }
    return message + " (HTTP " + status + ")";
}

_on("htmx:response:error", (e) => {
    let ctx = e.detail.ctx;
    if ((ctx.hx?.trigger || "").includes("swl-error")) {
        return;  // a FailResponse; its message is shown by the swl-error handler
    }
    ui.error(_message_for_status(ctx.response.status));
});

_on("htmx:error", (e) => {
    let error = e.detail.error;
    if (error?.name === "AbortError") {
        return;  // replaced by a newer request (hx-sync) or cancelled
    }
    ui.error(error instanceof TypeError ? _get("error_network") : _get("error_server"));
});

/* Wait cursor while requests are running */
let _running = 0;
let _last_activity = Date.now();
_on("htmx:before:request", () => {
    _running++;
    _last_activity = Date.now();
    document.documentElement.classList.add("swl-wait");
});
_on("htmx:finally:request", () => {
    _running = Math.max(0, _running - 1);
    _last_activity = Date.now();
    if (_running == 0) {
        document.documentElement.classList.remove("swl-wait");
    }
});

/*
 * Resolves when the page has settled: no requests running and none for `quiet` ms. Placeholders
 * that load placeholders that load placeholders start their requests one after another, so a
 * single moment without requests is not enough. Gives up waiting after `max_wait` ms (for pages
 * that poll).
 */
function _settled(quiet = 100, max_wait = 5000) {
    let start = Date.now();
    return new Promise((resolve) => {
        (function check() {
            let now = Date.now();
            if ((_running === 0 && now - _last_activity >= quiet) || now - start >= max_wait) {
                resolve();
            } else {
                setTimeout(check, 25);
            }
        })();
    });
}

/*
 * Pressing Enter in a field submits its form. A bare <form> (no action, method or htmx request
 * attribute) only groups fields for SWL actions, so that would just reload the page: prevent it.
 */
_on("submit", (e) => {
    let form = e.target;
    if (form instanceof HTMLFormElement && !form.hasAttribute("action") && !form.hasAttribute("method")
            && !form.matches("[hx-post],[hx-get],[hx-put],[hx-patch],[hx-delete],[hx-action]")) {
        e.preventDefault();
    }
});

/* ---------------------------------------------------------------- API */

/*
 * Post to an action from javascript; the response is handled like any other.
 * values: an object, a JSON string ('{"a": 1}') or a query string ("a=1&b=2").
 */
function swl_action(action, values) {
    if (typeof values === "string") {
        values = values.trim().startsWith("{") ? JSON.parse(values) : Object.fromEntries(new URLSearchParams(values));
    }
    return htmx.ajax("POST", action, {values: values || {}, swap: "none"});
}

/*
 * Post to an action once the page has loaded and its placeholders have loaded too, so the action
 * can hydrate elements inside them. Used by swl/kickstart.j2 to rebuild a page from a deep link.
 */
async function kickstart(action, values) {
    if (document.readyState !== "complete") {
        await new Promise((resolve) => window.addEventListener("load", resolve, {once: true}));
    }
    await _settled();
    return swl_action(action, values);
}

/* Reload a placeholder, optionally with extra context. */
function rehydrate(placeholder_id, context) {
    let elem = document.getElementById(placeholder_id);
    if (elem) {
        htmx.trigger(elem, REFRESH_EVENT, {context: context || {}}, false);
    }
}

export { swl_action, kickstart, rehydrate, ui };
