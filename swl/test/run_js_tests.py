## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

"""Runs the QUnit tests (js-test/*.test.js) in headless Chromium.

    pip install playwright && python -m playwright install chromium
    python -m swl.test.run_js_tests

Starts the test server (swl.test.server) on a free port, loads its page and waits for
QUnit. Exits with 1 when a test fails.
"""

import socket
import sys
import threading
import time

import uvicorn
from playwright.sync_api import sync_playwright

from swl.test.server import app

TIMEOUT_MS = 60_000


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port):
    server = uvicorn.Server(
        uvicorn.Config(app(), host="127.0.0.1", port=port, log_level="warning")
    )
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return server


def main():
    port = free_port()
    server = start_server(port)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{port}/")
            page.wait_for_function(
                "document.querySelector('#qunit-testresult-display .failed') !== null",
                timeout=TIMEOUT_MS,
            )
            summary = page.inner_text("#qunit-testresult-display")
            failed = int(page.inner_text("#qunit-testresult-display .failed"))
            failures = page.eval_on_selector_all(
                "#qunit-tests > li.fail",
                "items => items.map(li => li.querySelector('.module-name').textContent"
                " + ': ' + li.querySelector('.test-name').textContent"
                " + '\\n    ' + [...li.querySelectorAll('.fail .test-message')]"
                ".map(m => m.textContent).join('\\n    '))",
            )
            browser.close()
    finally:
        server.should_exit = True
    print(summary)
    for failure in failures:
        print("FAILED", failure)
    for error in errors:
        print("PAGE ERROR", error)
    return 1 if failed or errors else 0


if __name__ == "__main__":
    sys.exit(main())
