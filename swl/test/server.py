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

import pathlib

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from swl.actions import Actions
from swl.static_files import StaticFiles as SWLStaticFiles
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
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.9/dist/css/bootstrap.min.css"
        integrity="sha384-yEPZ7jP9S0QKiUQ0m3jjsO4ProIW7wvR9gXkI7JOGa2XVsw53Yke2bsdkBbjmmiX"
        crossorigin="anonymous">
    <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/jstree@3.3.17/dist/themes/default/style.min.css"
        integrity="sha384-clXSAz7utDyIerGEOzTe7HkSNZ7xrhxVuTY6yGNeF4LBW1zmtgF3AfFMP7iMZuRB"
        crossorigin="anonymous">
    <link rel="stylesheet" href="/static/swl/swl.css">


    <body>
        <div id="qunit"></div>
        <div id="qunit-fixture"></div>

        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.9/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-WyOxWvTyr1QaMPfiPJSv76iReVthorl5uWlFtZPyK0IEB0hGzo9y5Bp9mYanr8Bu"
          crossorigin="anonymous"></script>
        <script
          src="https://cdn.jsdelivr.net/npm/htmx.org@4.0.1/dist/htmx.min.js"
          integrity="sha384-Qp9rdC8H7EqOoX+nR0P3RPG2Noji+qdwJlGpfzwQJsfOpp3sGwIdSP9xO3+UlEhn"
          crossorigin="anonymous"></script>
        <script
          src="https://cdn.jsdelivr.net/npm/jquery@4.0.0/dist/jquery.min.js"
          integrity="sha384-fgGyf7Mo7DURSOMnOy7ed+dkq5Job205Gnzu6QIg0BOHKaqt4D76Dt8VlDCzcMHV"
          crossorigin="anonymous"></script>
        <script
          src="https://cdn.jsdelivr.net/npm/jstree@3.3.17/dist/jstree.min.js"
          integrity="sha384-foAvcRZ1cqpr2BrR53KQxGncZUQ2bYIq4y98ZBY0fNoWNXZW02MnL+fJ/lIyfyC+"
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
                app=SWLStaticFiles(directory=this_dir.parent / "static"),
                name="static",
            ),
        ],
    )


if __name__ == "__main__":
    uvicorn.run(app(), host="0.0.0.0", port=8000)
