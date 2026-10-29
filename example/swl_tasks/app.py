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

"""
Wires the example together: SWL, the actions, the pages, sessions and the websocket.
"""

from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from markupsafe import Markup

from seecr_stdlib.config import Config

from swl import SWL, static_dir
from swl.dispatcher import Dispatcher
from swl.frameworks import FrameworkCookieMiddleware
from swl.session import SessionAuthBackend, SessionSecretKey
from swl.userbase import Userbase
from swl.views import account

from . import views
from .store import TaskStore

__all__ = ["create_app", "DEMO_USER", "DEMO_PASSWORD"]

here = Path(__file__).parent

DEMO_USER = "demo"
DEMO_PASSWORD = "demo-password"


async def page(request, swl, store, **kwargs):
    """The task list page, for "/" and for "/tasks/<task id>/<tab>" (see views.page_url).

    The page is rendered as it was when the url was set: filters from the query
    parameters, the selected task and tab from the path. The detail panel is rendered
    right here, so a reload shows it without an extra request; the list loads itself (its
    placeholder) with the filters and the selection from the #filters form."""
    tab = request.path_params.get("tab", views.TABS[0])
    screen = views.screen_from(
        {
            "q": request.query_params.get("q", ""),
            "status": request.query_params.get("status", "all"),
            "selected_task": request.path_params.get("task_id"),
            "selected_tab": tab,
        }
    )
    detail_html = Markup(
        views.render_detail(swl, store, screen["task_id"], screen["tab"])
    )
    if screen["task_id"] and store.get(screen["task_id"]) is None:
        screen["task_id"] = None  # an old link: show that, but don't keep it selected
    return swl.template_response(
        request,
        "tasks/page.j2",
        {
            "title": "SWL Tasks",
            "body_class": "",
            "user": request.user,
            "statuses": views.STATUSES,
            **screen,
            "selection_html": views.render_selection(screen["task_id"], screen["tab"]),
            "detail_html": detail_html,
        },
    )


async def login_page(request, swl, **kwargs):
    return swl.template_response(
        request,
        "tasks/login.j2",
        {
            "title": "Log in - SWL Tasks",
            "body_class": "",
            "next": request.session.get("next", "/"),
            "demo_user": DEMO_USER,
            "demo_password": DEMO_PASSWORD,
        },
    )


def create_app(data_dir, userbase=None, framework="swl"):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if userbase is None:
        userbase = Userbase(data_dir / "users")
    if not userbase.all_users():
        userbase.create(DEMO_USER, DEMO_PASSWORD, admin=True)

    store = TaskStore(data_dir / "tasks.json")
    dispatcher = Dispatcher()

    # SWL: our templates first, then SWL's own (swl/base.j2, swl/modal.j2, ...).
    # "ui.framework" chooses the CSS framework: "swl" (SWL's own swl-base.css, no
    # framework), "bootstrap", "tabler" or "bulma". The templates use SWL.ui for their
    # classes, so they work with each.
    swl = SWL(
        config=Config({"ui": {"framework": framework}}), templates=[here / "templates"]
    )
    swl.register_modules(account, views)  # account: login, users and password dialogs
    swl.register_action_kwargs(userbase=userbase, store=store, dispatcher=dispatcher)
    swl.add_template_globals(VERSION=swl.SWL_VERSION)

    app = Starlette(
        routes=[
            swl.action_route,  # /action/<hash>: all actions
            Route("/", swl.endpoint(page, redirect="/login")),
            Route("/tasks/{task_id}", swl.endpoint(page, redirect="/login")),
            Route("/tasks/{task_id}/{tab}", swl.endpoint(page, redirect="/login")),
            Route("/login", swl.endpoint(login_page, authenticated=False)),
            Route("/logout", swl.endpoint(account.logout, authenticated=False)),
            WebSocketRoute("/ws", dispatcher.endpoint),  # change notifications
            # swl.js etc.
            Mount("/static", StaticFiles(directory=static_dir), name="static"),
            Mount("/example", StaticFiles(directory=here / "static"), name="example"),
        ],
        middleware=[
            # the framework switch in the page (style_switch.j2) sets this cookie
            Middleware(FrameworkCookieMiddleware, cookie="swl_framework"),
            Middleware(
                SessionMiddleware,
                secret_key=SessionSecretKey(data_dir / "session.key").key,
            ),
            Middleware(
                AuthenticationMiddleware, backend=SessionAuthBackend(userbase=userbase)
            ),
        ],
    )
    app.state.swl = swl
    app.state.store = store
    return app
