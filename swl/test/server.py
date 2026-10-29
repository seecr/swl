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

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.routing import Route, Mount

import uvicorn
import pathlib

from swl.actions import Actions
from swl.test.views import VIEWS


this_dir = pathlib.Path(__file__).parent
test_dir = this_dir / "js-test"


async def homepage(request):
    return HTMLResponse(
        """
<!DOCTYPE html>
<html>
    <meta charset="utf-8">
    <title>QUnit</title>
    <meta name="htmx-config" content='{"noSwap": [204, 304, "4xx", "5xx"]}'>
    <link rel="stylesheet" href="https://code.jquery.com/qunit/qunit-2.25.0.css">
    <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB"
        crossorigin="anonymous">


    <body>
        <div id="qunit"></div>
        <div id="qunit-fixture"></div>

        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI"
          crossorigin="anonymous"></script>
        <script
          src="https://cdn.jsdelivr.net/npm/htmx.org@4.0.0/dist/htmx.min.js"
          integrity="sha384-BvJpBiO8Kh31EqtJe5DRIeWrHWnCGkwytKs9NKFi86Hhw96dEqdEMzZDeK9iEGTc"
          crossorigin="anonymous"></script>
        <script src="/static/swl/swl-run.js" id="swl-run" type="module"></script>

        <script src="https://code.jquery.com/qunit/qunit-2.25.0.js"></script>"""
        + "".join(
            [
                f'<script src="/test/{p.name}" type="module"></script>'
                for p in test_dir.glob("*.test.js")
            ]
        )
        + """
    </body>
</html>"""
    )


def app():
    this_dir = pathlib.Path(__file__).parent

    actions = Actions(key=lambda name: name)
    actions.register_module(*VIEWS.modules)

    return Starlette(
        debug=True,
        routes=[
            Route("/", homepage),
            Route(
                "/action/{action:str}", endpoint=actions.handle, methods=["GET", "POST"]
            ),
            Mount("/test", app=StaticFiles(directory=test_dir), name="test"),
            Mount(
                "/static",
                app=StaticFiles(directory=this_dir.parent / "static"),
                name="static",
            ),
        ],
    )


if __name__ == "__main__":
    uvicorn.run(app(), host="0.0.0.0", port=8000)
