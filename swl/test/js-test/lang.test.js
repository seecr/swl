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
 * lang.js: the texts for swl.js come from the page (swl/base.j2 renders them in the page's
 * language as <script type="application/json" id="swl-lang">).
 */

QUnit.module("lang.js", () => {
    QUnit.test("texts from the page", async (assert) => {
        let elem = document.createElement("script");
        elem.type = "application/json";
        elem.id = "swl-lang";
        elem.textContent = JSON.stringify({confirm: "Bevestigen", yes: "Ja"});
        document.head.appendChild(elem);
        try {
            // a fresh copy of the module, which reads the element on first use
            const lang = await import("/static/swl/lang.js?embedded");
            await lang.set_lang("de_DE");  // ignored: the page has its texts
            assert.equal(lang._get("confirm"), "Bevestigen");
            assert.equal(lang._get("yes"), "Ja");
            assert.equal(lang._get("unknown_key"), "unknown_key");
        } finally {
            elem.remove();
        }
    });
});
