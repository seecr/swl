/* begin license *
 *
 * "SWL"(Seecr Web Lib) makes developing webbased apps easier
 *
 * Copyright (C) 2024, 2026 Seecr (Seek You Too B.V.) https://seecr.nl
 *
 * This file is part of "Seecr Web Lib"
 *
 * "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
 * SPDX-License-Identifier: MIT
 *
 * end license */

/*
 * Browser tests for SWL on htmx. The actions are in swl/test/views.
 * swl-run.js is loaded by the test page, so all SWL event handlers are active.
 */

import { swl_action, rehydrate } from "/static/swl/swl.js";

const DIALOG = `
    <dialog class="swl-dialog">
        <div class="swl-dialog-header"><h5><i></i><span></span></h5></div>
        <div id="swl-dialog-msg"></div>
        <button class="swl-btn-decline"></button>
        <button class="swl-btn-confirm"></button>
        <button class="swl-btn-ok"></button>
    </dialog>`;

const MODAL = `
    <dialog id="swl-modal" class="swl-modal swl-modal-lg">
        <div id="modal-content" class="swl-modal-box"></div>
    </dialog>`;

/* An application's own Bootstrap modal markup (still supported) */
const BOOTSTRAP_MODAL = `
    <div id="swl-modal" class="modal">
        <div id="modal-dialog" class="modal-dialog modal-lg">
            <div id="modal-content" class="modal-content"></div>
        </div>
    </div>`;

let recorded = [];
let requests = [];

function waitFor(condition, what = "condition", timeout = 2000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        (function poll() {
            if (condition()) {
                return resolve();
            }
            if (Date.now() - start > timeout) {
                return reject(new Error(`timeout waiting for ${what}; place="${text("#the_place")}"; requests=${JSON.stringify(requests)} recorded=${JSON.stringify(recorded)} dialog="${dialog_message()}"`));
            }
            setTimeout(poll, 20);
        })();
    });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector) => document.querySelector(selector);
const text = (selector) => $(selector)?.textContent ?? null;
const dialog_message = () => $("#swl-dialog-msg")?.textContent ?? "";
const dialog_shown = () => $(".swl-dialog")?.open === true;
const modal_shown = () => $("#swl-modal")?.open === true;
const modal_hidden = () => !$("#swl-modal")?.open;
const bs_modal_shown = () => $("#swl-modal")?.classList.contains("show");
const bs_modal_hidden = () => !$("#swl-modal")?.classList.contains("show") && !document.querySelector(".modal-backdrop");
const popover_open = (selector) => $(selector)?.matches(":popover-open") === true;
const press_escape = (elem) => elem.dispatchEvent(new Event("cancel", {cancelable: true}));

function fixture(html) {
    let elem = document.getElementById("qunit-fixture");
    elem.innerHTML = html;
    htmx.process(elem);
    return elem;
}

QUnit.module("swl on htmx", (hooks) => {
    let original_fetch;

    hooks.beforeEach(function () {
        $(".modal-backdrop")?.remove();
        document.body.classList.remove("modal-open");
        recorded = [];
        requests = [];
        window.swl_test_record = (kwargs) => { recorded.push(kwargs); };
        original_fetch = window.fetch;
        window.fetch = function (url, ...args) {
            requests.push(String(url));
            return original_fetch.call(this, url, ...args);
        };
    });

    hooks.afterEach(async function () {
        window.fetch = original_fetch;
        delete window.swl_test_record;
        const modal = document.getElementById("swl-modal");
        if (modal instanceof HTMLDialogElement) {
            modal.close();
        } else if (modal && modal.classList.contains("show")) {
            bootstrap.Modal.getInstance(modal).hide();
            await waitFor(bs_modal_hidden, "modal hidden");
        }
        document.querySelectorAll(":popover-open").forEach((elem) => elem.hidePopover());
        document.querySelectorAll("dialog[open]").forEach((elem) => elem.close());
        await sleep(20);  // let htmx finish the last request before the fixture is removed
    });

    QUnit.test("swl_action is available for inline scripts (kickstart)", (assert) => {
        assert.equal(typeof window.swl_action, "function");
        assert.equal(typeof window.swl.rehydrate, "function");
    });

    QUnit.test("a button posts its form and the response hydrates a placeholder", async (assert) => {
        fixture(`
            <div id="the_place"></div>
            <form>
                <input type="text" name="text" value="GO">
                <button id="btn" type="button" hx-post="/action/swl_echo" hx-vals='{"extra": "x"}'>Go</button>
            </form>`);
        $("#btn").click();
        await waitFor(() => text("#the_place") !== "", "hydrate");
        assert.equal(text("#the_place"), "extra=x&placeholder=btn&text=GO", "form fields, hx-vals and the element id as placeholder");
        assert.equal(text("#btn"), "Go", "the button itself is not swapped");
    });

    QUnit.test("a select posts on change", async (assert) => {
        fixture(`
            <div id="the_place"></div>
            <form>
                <select name="select" hx-post="/action/swl_change_select">
                    <option value="one">Een</option>
                    <option value="two">Twee</option>
                </select>
            </form>`);
        let select = $("select");
        select.value = "two";
        select.dispatchEvent(new Event("change", {bubbles: true}));
        await waitFor(() => text("#the_place") === "two", "hydrate");
        assert.ok(true);
    });

    QUnit.test("a placeholder loads itself and stores its recipe", async (assert) => {
        fixture(`<div id="the_place" hx-post="/action/swl_placeholder" hx-trigger="load, swl-refresh" hx-vals='{"some_id": "THE-ID"}'></div>`);
        await waitFor(() => text("#the_place") !== "", "load");
        assert.equal(text("#the_place"), "ID -> THE-ID");
        assert.equal($("#the_place").getAttribute("hx-vals"), '{"some_id":"THE-ID"}', "recipe context on the element");
    });

    QUnit.test("rehydrate reloads a placeholder with extra context", async (assert) => {
        fixture(`
            <div id="the_place"></div>
            <form>
                <input type="text" name="text" value="GO">
                <button id="btn-go" type="button" hx-post="/action/swl_hydrate_button">GO</button>
            </form>
            <form>
                <input type="hidden" name="text" value="AGAIN">
                <button id="btn-again" type="button" hx-post="/action/swl_rehydrate_button">AGAIN</button>
            </form>`);
        $("#btn-go").click();
        await waitFor(() => text("#the_place") === "GO", "hydrate");
        assert.equal($("#the_place").getAttribute("hx-post"), "/action/swl_hydrate_button", "recipe action stored on the element");

        $("#btn-again").click();
        await waitFor(() => text("#the_place") === "AGAIN", "rehydrate");
        assert.ok(true, "rehydrated with the context of the rehydrate");
    });

    QUnit.test("rehydrate only reloads the placeholder itself, not the placeholders around it", async (assert) => {
        fixture(`
            <div id="outer" hx-post="/action/swl_counted" hx-trigger="load, swl-refresh">
            </div>`);
        await waitFor(() => (text("#outer") || "").startsWith("count="), "outer load");
        let outer_text = text("#outer");
        $("#outer").insertAdjacentHTML("afterend", "");
        let inner = document.createElement("div");
        inner.id = "inner";
        inner.setAttribute("hx-post", "/action/swl_counted");
        inner.setAttribute("hx-trigger", "load, swl-refresh");
        $("#outer").appendChild(inner);
        htmx.process(inner);
        await waitFor(() => (text("#inner") || "").startsWith("count="), "inner load");

        let before = requests.length;
        rehydrate("inner", {extra: "yes"});
        await waitFor(() => text("#inner").endsWith("extra=yes"), "inner rehydrated");
        await sleep(100);
        assert.equal(requests.length, before + 1, "one request");
        assert.ok(text("#outer").startsWith(outer_text.split(" ")[0]), "outer not reloaded");
    });

    QUnit.test("a recipe makes any element rehydratable", async (assert) => {
        fixture(`
            <div id="plain"></div>
            <form>
                <input type="hidden" name="placeholder" value="plain">
                <button id="btn" type="button" hx-post="/action/swl_counted">Load</button>
            </form>
            <form>
                <input type="hidden" name="target" value="plain">
                <input type="hidden" name="extra" value="again">
                <button id="btn-rehydrate" type="button" hx-post="/action/swl_rehydrate">Rehydrate</button>
            </form>`);
        $("#btn").click();
        await waitFor(() => (text("#plain") || "").startsWith("count="), "hydrate");
        assert.equal($("#plain").getAttribute("hx-trigger"), "swl-refresh");

        $("#btn-rehydrate").click();
        await waitFor(() => text("#plain").endsWith("extra=again"), "rehydrate");
        assert.ok(true);
    });

    QUnit.test("hx-confirm uses the SWL dialog", async (assert) => {
        fixture(DIALOG + `
            <div id="the_place"></div>
            <form><button id="btn" type="button" hx-post="/action/swl_echo" hx-confirm="Are you sure?">Delete</button></form>`);
        $("#btn").click();
        await waitFor(dialog_shown, "dialog");
        assert.equal(dialog_message(), "Are you sure?");
        $(".swl-btn-decline").click();
        await sleep(100);
        assert.deepEqual(requests, [], "declined: no request");

        $("#btn").click();
        await waitFor(dialog_shown, "dialog");
        $(".swl-btn-confirm").click();
        await waitFor(() => text("#the_place") !== "", "request after confirm");
        assert.equal(requests.length, 1);
        assert.notOk(dialog_shown(), "dialog closed");
    });

    QUnit.test("Escape in the confirm dialog declines", async (assert) => {
        fixture(DIALOG + `<button id="btn" type="button" hx-post="/action/swl_echo" hx-confirm="Sure?">Go</button>`);
        $("#btn").click();
        await waitFor(dialog_shown, "dialog");
        press_escape($(".swl-dialog"));
        await sleep(100);
        assert.notOk(dialog_shown(), "dialog closed");
        assert.deepEqual(requests, [], "declined: no request");
    });

    QUnit.test("a FailResponse shows its message", async (assert) => {
        fixture(DIALOG + `<button id="btn" type="button" hx-post="/action/swl_fail">Go</button>`);
        $("#btn").click();
        await waitFor(dialog_shown, "dialog");
        assert.equal(dialog_message(), "That did not work");
        assert.equal(text("#btn"), "Go", "nothing swapped");
    });

    QUnit.test("failing requests are reported and not swapped into the page", async (assert) => {
        const cases = [
            ["/action/swl_error", "(HTTP 500)"],
            ["/action/swl_forbidden", "(HTTP 403)"],
            ["/action/does_not_exist", "(HTTP 404)"],
        ];
        for (const [url, expected] of cases) {
            fixture(DIALOG + `<button id="btn" type="button" hx-post="${url}">Go</button>`);
            $("#btn").click();
            await waitFor(dialog_shown, "dialog for " + url);
            assert.ok(dialog_message().endsWith(expected), `${url}: "${dialog_message()}"`);
            assert.equal(text("#btn"), "Go", "nothing swapped");
        }
    });

    QUnit.test("call: functions get their kwargs; an unknown function does not stop the others", async (assert) => {
        fixture(DIALOG);
        await swl_action("/action/swl_calls", {});
        await waitFor(() => recorded.length == 1, "call");
        assert.deepEqual(recorded, [{value: "after"}]);
        assert.ok(dialog_message().includes("swl_test_does_not_exist"), "unknown function reported");
    });

    QUnit.test("open_modal: native dialog, size class, call once per open", async (assert) => {
        fixture(MODAL + `
            <form>
                <input type="hidden" name="size" value="xl">
                <input type="hidden" name="call" value="swl_test_record">
                <button id="btn-open" type="button" hx-post="/action/swl_open_modal">Open</button>
                <button id="btn-close" type="button" hx-post="/action/swl_close_modal">Close</button>
            </form>`);
        $("#btn-open").click();
        await waitFor(() => modal_shown() && recorded.length == 1, "modal shown");
        assert.equal(text("#modal-content"), "This is the modal");
        assert.ok($("#swl-modal").classList.contains("swl-modal-xl"));
        assert.notOk($("#swl-modal").classList.contains("swl-modal-lg"));
        assert.ok($("#swl-modal").matches(":modal"), "modal: the rest of the page is inert");

        $("#btn-close").click();
        await waitFor(modal_hidden, "modal hidden");

        $("#btn-open").click();
        await waitFor(() => modal_shown() && recorded.length >= 2, "modal shown again");
        await sleep(100);
        assert.equal(recorded.length, 2, "call ran once per open");
    });

    QUnit.test("the modal closes with data-swl-close, not with Escape", async (assert) => {
        fixture(MODAL);
        await swl_action("/action/swl_open_modal", {});
        await waitFor(modal_shown, "modal shown");
        press_escape($("#swl-modal"));
        await sleep(50);
        assert.ok(modal_shown(), "Escape does not close it");
        $("#modal-content").insertAdjacentHTML("beforeend", `<button id="cancel" type="button" data-swl-close>Cancel</button>`);
        $("#cancel").click();
        assert.ok(modal_hidden(), "closed");
    });

    QUnit.test("open_modal with an application's Bootstrap modal markup", async (assert) => {
        fixture(BOOTSTRAP_MODAL + `
            <form>
                <input type="hidden" name="size" value="xl">
                <button id="btn-open" type="button" hx-post="/action/swl_open_modal">Open</button>
                <button id="btn-close" type="button" hx-post="/action/swl_close_modal">Close</button>
            </form>`);
        $("#btn-open").click();
        await waitFor(bs_modal_shown, "modal shown");
        assert.ok($("#modal-dialog").classList.contains("modal-xl"));
        $("#btn-close").click();
        await waitFor(bs_modal_hidden, "modal hidden");
        assert.equal(document.querySelectorAll(".modal-backdrop").length, 0);
    });

    QUnit.test("hydrate_modal(call=...) calls the function when the modal is open", async (assert) => {
        fixture(MODAL);
        await swl_action("/action/swl_open_modal", {});
        await waitFor(modal_shown, "modal shown");
        await swl_action("/action/swl_hydrate_modal_call", {});
        await waitFor(() => recorded.length == 1, "call");
        assert.equal(text("#modal-content"), "Replaced content");
    });

    QUnit.test("contextmenu posts the click position and opens the menu there", async (assert) => {
        fixture(`
            <div id="swl-contextmenu" class="swl-contextmenu" popover></div>
            <span id="item" hx-post="/action/swl_contextmenu" hx-trigger="contextmenu prevent" hx-vals='{"item": "42"}'>x</span>`);
        let event = new MouseEvent("contextmenu", {bubbles: true, cancelable: true, clientX: 110, clientY: 120});
        $("#item").dispatchEvent(event);
        assert.ok(event.defaultPrevented, "browser menu suppressed");
        await waitFor(() => popover_open("#swl-contextmenu"), "menu shown");
        assert.equal(text("#swl-contextmenu"), "menu for 42");
        assert.equal($("#swl-contextmenu").style.left, (110 - 8) + "px");
        assert.equal($("#swl-contextmenu").style.top, (120 - 8) + "px");
    });

    QUnit.test("reset_form resets the form of the element that posted", async (assert) => {
        fixture(`
            <form>
                <input id="field" type="text" name="text" value="original">
                <button id="btn" type="button" hx-post="/action/swl_reset_form">Save</button>
            </form>`);
        $("#field").value = "changed";
        $("#btn").click();
        await waitFor(() => $("#field").value === "original", "reset");
        assert.ok(true);
    });

    QUnit.test("toast shows the text", async (assert) => {
        fixture(`<div id="toast" class="swl-toast" popover="manual"><div id="toast-body"></div></div>`);
        await swl_action("/action/swl_toast", {});
        await waitFor(() => popover_open("#toast"), "toast shown");
        assert.equal($("#toast-body").innerHTML, "Saved <b>it</b>");
        await waitFor(() => !popover_open("#toast"), "toast hidden after its delay");
    });

    QUnit.test("a second toast while the first is showing does not break", async (assert) => {
        let errors = [];
        let on_error = (e) => errors.push(e.message);
        window.addEventListener("error", on_error);
        fixture(`<div id="toast" class="swl-toast" popover="manual"><div id="toast-body"></div></div>`);
        await swl_action("/action/swl_toast", {});
        await waitFor(() => popover_open("#toast"), "first toast");
        await sleep(400);
        await swl_action("/action/swl_toast", {});
        await sleep(400);
        window.removeEventListener("error", on_error);
        assert.deepEqual(errors, []);
        assert.ok(popover_open("#toast"), "still showing: the second toast restarted the timer");
    });

    QUnit.test("session_store stores values", async (assert) => {
        window.sessionStorage.removeItem("swl_test_key");
        await swl_action("/action/swl_session_store", {});
        await waitFor(() => window.sessionStorage.getItem("swl_test_key") !== null, "stored");
        assert.deepEqual(JSON.parse(window.sessionStorage.getItem("swl_test_key")), {a: [1, 2]});
    });

    QUnit.test("data-swl-validate blocks the request when missing or false", async (assert) => {
        fixture(DIALOG + `
            <div id="the_place"></div>
            <form>
                <input type="hidden" name="a" value="1">
                <button id="missing" type="button" hx-post="/action/swl_echo" data-swl-validate="swl_test_no_validator">x</button>
                <button id="invalid" type="button" hx-post="/action/swl_echo" data-swl-validate="swl_test_invalid">x</button>
                <button id="valid" type="button" hx-post="/action/swl_echo" data-swl-validate="swl_test_valid">x</button>
            </form>`);
        window.swl_test_invalid = () => false;
        window.swl_test_valid = () => true;

        $("#missing").click();
        $("#invalid").click();
        await sleep(100);
        assert.deepEqual(requests, [], "nothing posted");
        assert.ok(dialog_message().includes("swl_test_no_validator"), "missing validator reported");

        $("#valid").click();
        await waitFor(() => text("#the_place") === "a=1&placeholder=valid", "posted");
        assert.equal(requests.length, 1);

        delete window.swl_test_invalid;
        delete window.swl_test_valid;
    });

    QUnit.test("swl_action accepts an object or a query string", async (assert) => {
        fixture(`<div id="the_place"></div>`);
        await swl_action("/action/swl_echo", {a: "1", b: "2"});
        await waitFor(() => text("#the_place") === "a=1&b=2", "object, got: " + text("#the_place"));
        await swl_action("/action/swl_echo", "c=3");
        await waitFor(() => text("#the_place") === "c=3", "string");
        assert.ok(true);
    });

    QUnit.test("a placeholder posts only its own values, not the fields inside it or around it", async (assert) => {
        fixture(`
            <form>
                <input type="hidden" name="around" value="1">
                <div id="the_place" hx-post="/action/swl_echo" hx-trigger="swl-refresh" hx-vals='{"own": "yes"}'>
                    <input type="hidden" name="inside" value="2">
                </div>
            </form>`);
        rehydrate("the_place", {extra: "x"});
        await waitFor(() => !$("#the_place input"), "hydrated");
        assert.equal(text("#the_place"), "extra=x&own=yes&placeholder=the_place");
    });

    QUnit.test("hx-include on a placeholder adds those fields, not the ones inside it", async (assert) => {
        fixture(`
            <form id="filter"><input type="hidden" name="q" value="abc"></form>
            <div id="the_place" hx-post="/action/swl_echo" hx-trigger="swl-refresh" hx-include="#filter">
                <input type="hidden" name="inside" value="2">
            </div>`);
        rehydrate("the_place");
        await waitFor(() => !$("#the_place input"), "hydrated");
        assert.equal(text("#the_place"), "placeholder=the_place&q=abc");
    });

    QUnit.test("kickstart waits until nested placeholders have loaded", async (assert) => {
        fixture(`<div id="outer" hx-post="/action/swl_slow_outer" hx-trigger="load"></div>`);
        await window.swl.kickstart("/action/swl_echo", {deep: "yes"});
        await waitFor(() => text("#the_place") === "deep=yes", "kickstarted action hydrated the inner placeholder");
        assert.ok(true);
    });

    QUnit.test("kickstart and swl_action accept a JSON string", async (assert) => {
        fixture(`<div id="the_place"></div>`);
        await window.swl.kickstart("/action/swl_echo", '{"a": "1", "b": "2"}');
        await waitFor(() => text("#the_place") === "a=1&b=2", "hydrated");
        assert.ok(true);
    });

    QUnit.test("Bootstrap tabs load their content when shown (hx-trigger show.bs.tab)", async (assert) => {
        fixture(`
            <form>
                <input type="hidden" name="item" value="42">
                <ul class="nav nav-tabs">
                    <li><button id="t1" type="button" class="nav-link active" data-bs-toggle="tab" data-bs-target="#p1"
                                hx-post="/action/swl_echo" hx-vals='{"tab": "overview"}' hx-trigger="load, show.bs.tab">Overview</button></li>
                    <li><button id="t2" type="button" class="nav-link" data-bs-toggle="tab" data-bs-target="#p2"
                                hx-post="/action/swl_echo" hx-vals='{"tab": "history"}' hx-trigger="show.bs.tab once">History</button></li>
                </ul>
            </form>
            <div class="tab-content">
                <div id="p1" class="tab-pane active"><div id="the_place"></div></div>
                <div id="p2" class="tab-pane"></div>
            </div>`);
        await waitFor(() => text("#the_place") !== "", "active tab loaded");
        assert.equal(text("#the_place"), "item=42&placeholder=t1&tab=overview", "the active tab loads with the page and posts its form");

        $("#t2").click();
        await waitFor(() => text("#the_place").includes("history"), "second tab");
        assert.ok($("#p2").classList.contains("active"), "Bootstrap switched the pane");

        $("#t1").click();
        await waitFor(() => text("#the_place").includes("overview"), "back to the first tab");
        assert.ok(true, "showing a tab again loads it again");

        let before = requests.length;
        $("#t2").click();
        await sleep(150);
        assert.equal(requests.length, before, "with 'once' a tab only loads the first time");
    });

    QUnit.test("Enter in a bare form does not reload the page", (assert) => {
        let elem = fixture(`
            <form id="bare"><input name="q"></form>
            <form id="real" method="post"><input name="q"></form>`);
        let bare = new SubmitEvent("submit", {bubbles: true, cancelable: true});
        $("#bare").dispatchEvent(bare);
        assert.ok(bare.defaultPrevented, "bare form not submitted");

        let real = new SubmitEvent("submit", {bubbles: true, cancelable: true});
        let stop = (e) => e.preventDefault();  // keep the test page; we only check SWL left it alone
        $("#real").addEventListener("submit", (e) => { assert.notOk(e.defaultPrevented, "form with method is left alone"); stop(e); });
        $("#real").dispatchEvent(real);
    });
});
