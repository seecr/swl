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
 * SWL's icons for swl.js, by name (swl/icons.py): the classes for "confirm", "error",
 * "info" and "saved". swl/base.j2 puts them in the page as
 * <script type="application/json" id="swl-icons">; a page without it (an own base
 * template) gets Bootstrap Icons.
 */
const SWL_ICONS = "swl-icons";
const BOOTSTRAP_ICONS = {
    confirm: "bi bi-question-diamond-fill",
    error: "bi bi-exclamation-circle-fill",
    info: "bi bi-info-circle-fill",
    saved: "bi bi-check2",
};

function _embedded() {
    let elem = document.getElementById(SWL_ICONS);
    try {
        return elem ? JSON.parse(elem.textContent) : {};
    } catch (error) {
        return {};
    }
}

function _icon(name) {
    return _embedded()[name] ?? BOOTSTRAP_ICONS[name] ?? "";
}

export { _icon };
