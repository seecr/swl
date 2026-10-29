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

import { swl_action, kickstart, rehydrate, ui } from "./swl.js"
import { set_lang } from "./lang.js"

// For inline scripts such as swl/kickstart.j2 and application code, which cannot import the module.
window.swl_action = swl_action;
window.swl = { action: swl_action, kickstart, rehydrate, ui };

set_lang(document.getElementById("swl-run")?.getAttribute("lang") || "en_US");
