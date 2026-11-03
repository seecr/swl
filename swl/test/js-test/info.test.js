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
 * The help balloon (swl/info.j2): an (i) button with popovertarget, the balloon a popover
 * that swl.js places next to it.
 */

import "/static/swl/swl.js";

const $ = (selector) => document.querySelector(selector);
const open = (selector) => $(selector).matches(":popover-open");
const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));

/* what swl/info.j2 renders, at a place on the screen */
function info(style = "", id = "info-1") {
    let fixture = document.getElementById("qunit-fixture");
    fixture.insertAdjacentHTML("beforeend", `
        <div style="position: fixed; ${style}">
            <button type="button" class="swl-info" popovertarget="${id}" aria-label="More information">i</button>
            <span id="${id}" class="swl-info-text" popover>The background of the page and its windows</span>
        </div>`);
    return [$(`[popovertarget="${id}"]`), $(`#${id}`)];
}

QUnit.module("help balloon", (hooks) => {
    hooks.afterEach(() => {
        document.querySelectorAll(":popover-open").forEach((elem) => elem.hidePopover());
        document.querySelectorAll("dialog[open]").forEach((elem) => elem.close());
    });

    QUnit.test("a click on the (i) shows the text below it; again: gone", async (assert) => {
        let [button, text] = info("top: 100px; left: 200px");
        button.click();
        await nextFrame();
        assert.ok(open("#info-1"), "open");
        assert.ok(text.hasAttribute("data-swl-placed"), "placed");
        assert.equal(getComputedStyle(text).visibility, "visible");
        let b = button.getBoundingClientRect();
        let t = text.getBoundingClientRect();
        assert.ok(Math.abs(t.top - (b.bottom + 6)) < 1, `just below the button (${t.top}, ${b.bottom})`);
        assert.ok(t.left <= b.left && t.right >= b.right, "centred on the button");
        button.click();
        await nextFrame();
        assert.notOk(open("#info-1"), "closed");
        assert.notOk(text.hasAttribute("data-swl-placed"));
    });

    QUnit.test("an auto popover: the browser closes it on a click elsewhere or Escape", (assert) => {
        // (light dismiss needs real clicks and keys; scripted ones do not count)
        let [, text] = info("top: 100px; left: 200px");
        assert.equal(text.popover, "auto");
    });

    QUnit.test("at the bottom of the window: above the button", async (assert) => {
        let [button, text] = info("bottom: 4px; left: 200px");
        button.click();
        await nextFrame();
        let b = button.getBoundingClientRect();
        let t = text.getBoundingClientRect();
        assert.ok(t.bottom <= b.top, `above (${t.bottom}, ${b.top})`);
    });

    QUnit.test("at the right edge: inside the window", async (assert) => {
        let [button, text] = info("top: 100px; right: 0");
        button.click();
        await nextFrame();
        let t = text.getBoundingClientRect();
        assert.ok(t.right <= window.innerWidth - 8 + 0.5, `${t.right} <= ${window.innerWidth - 8}`);
        assert.ok(t.left >= 8);
    });

    QUnit.test("in an open modal: the balloon is on top of it", async (assert) => {
        let fixture = document.getElementById("qunit-fixture");
        fixture.insertAdjacentHTML("beforeend", `
            <dialog id="info-modal" class="swl-modal"><div class="swl-modal-box">
                <button type="button" class="swl-info" popovertarget="info-2">i</button>
                <span id="info-2" class="swl-info-text" popover>Help in a modal</span>
            </div></dialog>`);
        $("#info-modal").showModal();
        $("[popovertarget=info-2]").click();
        await nextFrame();
        let t = $("#info-2").getBoundingClientRect();
        let hit = document.elementFromPoint(t.left + t.width / 2, t.top + t.height / 2);
        assert.ok($("#info-2").contains(hit), "the balloon, not the modal, is under its centre");
        $("#info-modal").close();
    });
});
