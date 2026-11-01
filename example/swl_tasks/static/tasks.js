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
 * Javascript of the example. These functions are called by the server with
 * swl.success().call("name", **kwargs): SWL calls window[name](kwargs).
 */

/* Called by the tasks_list action with the number of open tasks and the counts as text,
 * in the page's language. */
function show_counts({open, text}) {
    let badge = document.getElementById("task-counts");
    if (badge) {
        badge.textContent = text;
    }
    document.title = open > 0 ? `(${open}) SWL Tasks` : "SWL Tasks";
}

/* Called when the task form is shown in the modal (open_modal(..., call="focus_title")). */
function focus_title() {
    let title = document.getElementById("task-title");
    if (title) {
        title.focus();
        title.select();
    }
}

/*
 * The switches in the top bar (templates/tasks/style_switch.j2). The language is the cookie
 * "swl_lang" that swl.i18n_middleware reads (app.py), so the page reloads.
 * The CSS framework is a cookie that the server reads (FrameworkCookieMiddleware in app.py), so
 * the page reloads; light/dark/auto is swl/static/swl/theme.js and changes the page right away.
 */
const THEME_ICON = {auto: "bi-circle-half", light: "bi-sun", dark: "bi-moon-stars"};

function show_theme_mode(mode) {
    let button = document.getElementById("theme-switch");
    if (button) {
        let icon = THEME_ICON[mode];
        // the titles in the page's language: data-title-auto, -light, -dark (style_switch.j2)
        let title = button.dataset["title" + mode[0].toUpperCase() + mode.slice(1)];
        button.querySelector("i").className = "bi " + icon;
        button.title = title;
        button.setAttribute("aria-label", title);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("language-switch")?.addEventListener("change", (e) => {
        document.cookie = `swl_lang=${e.target.value}; path=/; max-age=31536000; samesite=lax`;
        window.location.reload();
    });
    document.getElementById("framework-switch")?.addEventListener("change", (e) => {
        document.cookie = `swl_framework=${e.target.value}; path=/; max-age=31536000; samesite=lax`;
        window.location.reload();
    });
    document.getElementById("theme-switch")?.addEventListener("click", () => {
        let modes = window.swl_theme.modes;
        window.swl_theme.set(modes[(modes.indexOf(window.swl_theme.get()) + 1) % modes.length]);
    });
    document.addEventListener("swl-theme", (e) => show_theme_mode(e.detail.mode));
    show_theme_mode(window.swl_theme?.get() ?? "auto");
});
