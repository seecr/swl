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
 * The colour field (color_input in swl/inputs.j2): a hidden input, a button that opens a
 * panel with colours and red/green/blue fields.
 */

import { set_color } from "/static/swl/swl.js";

const $ = (selector) => document.querySelector(selector);
const open = () => $("#c1-colors").matches(":popover-open");
const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));

/* what color_input renders (with three colours), in a form */
function color_field(value = "#1c7ed6", clear = false) {
    let fixture = document.getElementById("qunit-fixture");
    let swatch = (hex) => `<button type="button" class="swl-color-swatch" data-swl-color="${hex}"
        style="background-color: ${hex}" title="${hex}" aria-label="${hex}"
        aria-pressed="${hex === value}"></button>`;
    let channel = (letter) => `<label>${letter} <input type="number" class="form-control" min="0"
        max="255" step="1" inputmode="numeric" aria-label="${letter}"></label>`;
    fixture.insertAdjacentHTML("beforeend", `
        <form id="f1" style="position: fixed; top: 100px; left: 200px">
          <div class="swl-field">
            <label for="c1">Colour</label>
            <div class="swl-color">
              <input type="hidden" name="color" value="${value}">
              <button type="button" class="swl-color-button" id="c1" popovertarget="c1-colors">
                <span class="swl-color-sample" style="background-color: ${value}"></span>
                <span class="swl-color-value">${value}</span>
              </button>
              <div class="swl-color-panel" id="c1-colors" popover>
                <div class="swl-color-swatches">
                  ${swatch("#e03131")}${swatch("#1c7ed6")}${swatch("#ffffff")}
                </div>
                ${clear ? `<button type="button" class="swl-color-clear" aria-pressed="${!value}">
                  <span class="swl-color-sample"></span>No colour</button>` : ""}
                <div class="swl-color-custom">
                  <span class="swl-color-custom-label">Custom colour</span>
                  ${channel("R")}${channel("G")}${channel("B")}
                  <span class="swl-color-sample"></span>
                </div>
              </div>
            </div>
          </div>
        </form>`);
    let form = $("#f1");
    let heard = [];
    for (let type of ["input", "change"]) {
        form.addEventListener(type, (e) => heard.push(`${type} ${e.target.name || e.target.type}`));
    }
    return {
        form, heard,
        input: $("#f1 input[name=color]"),
        button: $("#c1"),
        channels: [...document.querySelectorAll("#f1 .swl-color-custom input")],
    };
}

function type_in(channel, value) {
    channel.value = value;
    channel.dispatchEvent(new Event("input", {bubbles: true}));
}

QUnit.module("colour field", (hooks) => {
    hooks.afterEach(() => {
        document.querySelectorAll(":popover-open").forEach((elem) => elem.hidePopover());
    });

    QUnit.test("the button opens the panel below it, the chosen colour has the focus", async (assert) => {
        let {button, channels} = color_field();
        button.click();
        await nextFrame();
        assert.ok(open(), "open");
        let b = button.getBoundingClientRect();
        let p = $("#c1-colors").getBoundingClientRect();
        assert.ok(Math.abs(p.top - (b.bottom + 6)) < 1, `just below the button (${p.top}, ${b.bottom})`);
        assert.equal(document.activeElement, $('[data-swl-color="#1c7ed6"]'));
        assert.deepEqual(channels.map((c) => c.value), ["28", "126", "214"], "red/green/blue");
    });

    QUnit.test("a click on a colour: the value, events, and the panel closes", async (assert) => {
        let {button, input, heard} = color_field();
        button.click();
        await nextFrame();
        $('[data-swl-color="#e03131"]').click();
        await nextFrame();
        assert.equal(input.value, "#e03131");
        assert.deepEqual(heard, ["input color", "change color"]);
        assert.notOk(open(), "closed");
        assert.equal(document.activeElement, button, "focus back on the button");
        assert.equal($(".swl-color-value").textContent, "#e03131");
        assert.equal(getComputedStyle($(".swl-color-button .swl-color-sample")).backgroundColor,
            "rgb(224, 49, 49)");
        assert.equal($('[data-swl-color="#e03131"]').getAttribute("aria-pressed"), "true");
        assert.equal($('[data-swl-color="#1c7ed6"]').getAttribute("aria-pressed"), "false");
    });

    QUnit.test("red/green/blue: the colour follows the typing; the form only hears the field", async (assert) => {
        let {button, input, channels, heard} = color_field();
        button.click();
        await nextFrame();
        type_in(channels[0], "255");
        assert.equal(input.value, "#ff7ed6");
        type_in(channels[1], "300");
        assert.equal(input.value, "#ff7ed6", "300 is not a colour value");
        type_in(channels[1], "");
        assert.equal(input.value, "#ff7ed6", "nor is nothing");
        type_in(channels[1], "0");
        assert.equal(input.value, "#ff00d6");
        channels[1].dispatchEvent(new Event("change", {bubbles: true}));
        assert.deepEqual(heard, ["input color", "input color", "change color"]);
        assert.ok(open(), "still open");
        assert.equal($(".swl-color-custom .swl-color-sample").style.backgroundColor, "rgb(255, 0, 214)");
        assert.ok([...document.querySelectorAll(".swl-color-swatch")]
            .every((s) => s.getAttribute("aria-pressed") === "false"), "none of the colours");
    });

    QUnit.test("Enter in red/green/blue closes the panel and does not send the form", async (assert) => {
        let {button, form, channels, heard} = color_field();
        let sent = 0;
        form.addEventListener("submit", (e) => { e.preventDefault(); sent++; });
        button.click();
        await nextFrame();
        channels[2].value = "0";
        channels[2].dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true, cancelable: true}));
        await nextFrame();
        assert.notOk(open(), "closed");
        assert.equal(sent, 0);
        assert.deepEqual(heard, ["input color", "change color"]);
        assert.equal(document.activeElement, button);
    });

    QUnit.test("arrow keys move through the colours", async (assert) => {
        let {button} = color_field("#e03131");
        button.click();
        await nextFrame();
        let key = (k) => document.activeElement.dispatchEvent(
            new KeyboardEvent("keydown", {key: k, bubbles: true, cancelable: true}));
        key("ArrowRight");
        assert.equal(document.activeElement.dataset.swlColor, "#1c7ed6");
        key("ArrowDown");  // no next row: the last one
        assert.equal(document.activeElement.dataset.swlColor, "#ffffff");
        key("ArrowLeft");
        assert.equal(document.activeElement.dataset.swlColor, "#1c7ed6");
    });

    QUnit.test("No colour: back to none, the events, the panel closes", async (assert) => {
        let {button, input, heard, channels} = color_field("#e03131", true);
        button.click();
        await nextFrame();
        assert.equal($(".swl-color-clear").getAttribute("aria-pressed"), "false");
        $(".swl-color-clear").click();
        await nextFrame();
        assert.equal(input.value, "");
        assert.deepEqual(heard, ["input color", "change color"]);
        assert.notOk(open(), "closed");
        assert.equal($(".swl-color-value").textContent, "");
        let sample = $(".swl-color-button .swl-color-sample");
        assert.notOk(sample.hasAttribute("style"), "no style left: struck through");
        assert.notEqual(getComputedStyle(sample).backgroundImage, "none");
        assert.equal($(".swl-color-clear").getAttribute("aria-pressed"), "true");
        assert.deepEqual(channels.map((c) => c.value), ["", "", ""]);
        button.click();
        await nextFrame();
        assert.equal(document.activeElement, $(".swl-color-clear"), "focus on No colour");
    });

    QUnit.test("set_color from code, with or without events", (assert) => {
        let {input, heard} = color_field("");
        set_color(input, "#00FF00");
        assert.equal(input.value, "#00ff00");
        assert.equal($(".swl-color-value").textContent, "#00ff00");
        assert.deepEqual(heard, []);
        set_color($(".swl-color-button"), "#ffffff", true);
        assert.deepEqual(heard, ["input color", "change color"]);
        assert.equal($('[data-swl-color="#ffffff"]').getAttribute("aria-pressed"), "true");
        assert.equal(window.swl.set_color, set_color, "also window.swl.set_color");
        assert.throws(() => set_color(input, "red"), /not a colour/);
    });
});
