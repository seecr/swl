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

const SWL_LANG = "swl-lang";

async function set_lang(locale) {
    try {
        const translations = await import(`./lang/${locale}.json`, { with: { type: "json" } });
        window.localStorage.setItem(SWL_LANG, JSON.stringify(translations.default));
    } catch (error) {
        const defaultTranslations = await import('./lang/en_US.json', { with: { type: "json" } });
        window.localStorage.setItem(SWL_LANG, JSON.stringify(defaultTranslations.default));
    }
}

function _get(key) {
    let values = window.localStorage.getItem(SWL_LANG);

    if (!values) {
        return key;
    }
    let value = JSON.parse(values)[key];
    return (value === undefined) ? key : value;
}


export { set_lang, _get };
