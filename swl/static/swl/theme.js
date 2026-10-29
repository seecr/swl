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
 * Light, dark or automatic (the computer's setting) colours, for every framework SWL supports:
 * sets data-theme (swl-base.css, Bulma) and data-bs-theme (Bootstrap) on <html>, and remembers
 * the choice in localStorage. Load it in <head>, not as a module, so the page is painted in the
 * right colours straight away:
 *
 *     {% block head_extra %}<script src="/static/swl/theme.js"></script>{% endblock %}
 *
 * swl_theme.set("dark") / swl_theme.set("light") / swl_theme.set("auto"); swl_theme.get().
 * A "swl-theme" event on document tells others (e.g. a switch button) about a change.
 */
(function () {
    const KEY = "swl-theme";
    const MODES = ["auto", "light", "dark"];
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function get() {
        try {
            let mode = window.localStorage.getItem(KEY);
            return MODES.includes(mode) ? mode : "auto";
        } catch (e) {
            return "auto";
        }
    }

    function apply(mode) {
        let theme = mode === "dark" || (mode === "auto" && media.matches) ? "dark" : "light";
        let root = document.documentElement;
        root.setAttribute("data-theme", theme);
        root.setAttribute("data-bs-theme", theme);
        root.setAttribute("data-swl-theme-mode", mode);
    }

    function set(mode) {
        if (!MODES.includes(mode)) {
            throw new Error("swl_theme.set: one of " + MODES.join(", "));
        }
        try {
            window.localStorage.setItem(KEY, mode);
        } catch (e) {
            // private window: works for this page only
        }
        apply(mode);
        document.dispatchEvent(new CustomEvent("swl-theme", {detail: {mode: mode}}));
    }

    apply(get());
    media.addEventListener("change", () => apply(get()));
    window.swl_theme = {get: get, set: set, modes: MODES};
})();
