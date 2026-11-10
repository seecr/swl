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
 * SWL's layouts (swl/templates/swl/layouts/), loaded by them: closes a dropdown
 * (<details class="swl-layout-dropdown">) on a click outside it, on Escape and after a
 * click on one of its items; closes the menu popovers after a click on an action in them;
 * and keeps the clock of the "retro" layout going.
 */
(function () {
    const OPEN_DROPDOWNS = "details.swl-layout-dropdown[open]";
    const MENU_POPOVERS = "#swl-layout-nav, #swl-retro-startmenu";

    function closeDropdowns(except) {
        for (let details of document.querySelectorAll(OPEN_DROPDOWNS)) {
            if (details !== except) {
                details.open = false;
            }
        }
    }

    document.addEventListener("click", (e) => {
        let details = e.target.closest?.("details.swl-layout-dropdown");
        closeDropdowns(details);
        if (details && e.target.closest(".swl-layout-dropdown-menu")) {
            details.open = false;  // an item was chosen
        }
        let popover = e.target.closest?.(MENU_POPOVERS);
        if (popover && e.target.closest("button[hx-post]") && popover.matches(":popover-open")) {
            popover.hidePopover();  // an action (e.g. a dialog) was chosen
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeDropdowns(null);
        }
    });

    function tick() {
        let time = new Date().toLocaleTimeString(document.documentElement.lang || undefined,
                                                  {hour: "2-digit", minute: "2-digit"});
        for (let clock of document.querySelectorAll(".swl-retro-clock")) {
            clock.textContent = time;
        }
    }
    if (document.querySelector(".swl-retro-clock")) {
        tick();
        setInterval(tick, 10000);
    }
})();
