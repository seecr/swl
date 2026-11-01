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
 * SWL's texts for swl.js. swl/base.j2 puts them in the page, in the language of the page:
 * <script type="application/json" id="swl-lang">. A page without it (an own base
 * template) falls back to the JSON files in lang/, chosen with the lang attribute of
 * swl-run.js and kept in localStorage (deprecated).
 */
const SWL_LANG = "swl-lang";
let embedded;

function _embedded() {
    if (embedded === undefined) {
        let elem = document.getElementById(SWL_LANG);
        try {
            embedded = elem ? JSON.parse(elem.textContent) : null;
        } catch (error) {
            embedded = null;
        }
    }
    return embedded;
}

async function set_lang(locale) {
    if (_embedded()) {
        return;
    }
    try {
        const translations = await import(`./lang/${locale}.json`, { with: { type: "json" } });
        window.localStorage.setItem(SWL_LANG, JSON.stringify(translations.default));
    } catch (error) {
        const defaultTranslations = await import('./lang/en_US.json', { with: { type: "json" } });
        window.localStorage.setItem(SWL_LANG, JSON.stringify(defaultTranslations.default));
    }
}

function _get(key) {
    let values = _embedded();
    if (!values) {
        let stored = window.localStorage.getItem(SWL_LANG);
        values = stored ? JSON.parse(stored) : null;
    }
    if (!values) {
        return key;
    }
    let value = values[key];
    return (value === undefined) ? key : value;
}


export { set_lang, _get };
