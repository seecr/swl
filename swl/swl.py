## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2025 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

__all__ = ["SWL"]


import pathlib

import jinja2
from markupsafe import Markup, escape
from starlette.middleware import Middleware
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from swl.actions import Actions
from swl.frameworks import framework, requested_framework
from swl.i18n import COOKIE, I18n, I18nMiddleware
from swl.i18n import install as install_i18n
from swl.i18n import js_messages
from swl.icons import icons
from swl.menu import Menu
from swl.resources import WebResources
from swl.responses import FailResponse, SuccessResponse
from swl.routes_endpoint import make_routes_route

from ._version import __version__

static_dir = pathlib.Path(__file__).parent / "static"
templates_dir = pathlib.Path(__file__).parent / "templates"


class SWL:
    SWL_VERSION = __version__.split("+")[0]

    def __init__(self, config, templates=[]):
        self._config = config
        self._actions = Actions(
            path=self._config.get("actions.path", "/action"),
            key=None if self._config.get("actions.hash", True) is True else lambda x: x,
        )
        self._actions.register_kwarg("swl", self)
        # "ui.framework": "swl", "bootstrap" (default) or "bulma"; "paths.resources"
        # replaces its web resources with your own file, "paths.extra_resources" (a file
        # or a list of files) adds to them. FrameworkCookieMiddleware can
        # choose another one per request (swl/frameworks.py).
        self._framework = framework(self._config.get("ui.framework"))
        # "ui.icons": the classes of SWL's own icons (Bootstrap Icons by default);
        # "ui.icons_stylesheet" replaces the Bootstrap Icons stylesheet, or with false
        # leaves it out (swl/icons.py)
        self._icons = icons(self._config.get("ui.icons"))
        self._icons_stylesheet = self._config.get("ui.icons_stylesheet")
        self._web_resources_cache = {}
        self._templates = Jinja2Templates(
            env=jinja2.Environment(
                undefined=jinja2.StrictUndefined,
                loader=jinja2.FileSystemLoader([*templates, templates_dir]),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        )

        # translations: "i18n.locales" (default ["en"]); swl.i18n_middleware chooses
        # the language per request (swl/i18n.py)
        self.i18n = I18n(
            locales=self._config.get("i18n.locales"),
            cookie=self._config.get("i18n.cookie", COOKIE),
        )
        install_i18n(self._templates.env, self.i18n)

        # the menu for SWL's layouts (swl/templates/swl/layouts/), see set_menu
        self.menu = Menu()

        self._templates.env.globals["SWL"] = self
        self._templates.env.globals["register"] = self._actions.register

        self.routes_route = make_routes_route(self._config.get("routes.allowlist"))

    @property
    def cdn_url(self):
        return self._config.get("urls.cdn", "https://cdn.jsdelivr.net")

    def _current_framework(self):
        return requested_framework() or self._framework

    @property
    def _web_resources(self):
        fw = self._current_framework()
        if fw.name not in self._web_resources_cache:
            self._web_resources_cache[fw.name] = WebResources(
                self._config.get("paths.resources") or fw.resources,
                self.cdn_url,
                extra=self._config.get("paths.extra_resources") or (),
                icons_stylesheet=self._icons_stylesheet,
            )
        return self._web_resources_cache[fw.name]

    @property
    def framework(self):
        """The name of the CSS framework: "swl", "bootstrap" or "bulma"."""
        return self._current_framework().name

    @property
    def ui(self):
        """CSS classes for form elements and buttons in this framework
        (swl/frameworks.py)."""
        return self._current_framework().classes

    @property
    def icons(self):
        """The CSS classes of SWL's own icons, by name: {{ SWL.icons.close }}
        (swl/icons.py)."""
        return self._icons

    @property
    def js_icons(self):
        """SWL's icons for swl.js (swl/base.j2 puts them in the page)."""
        return dict(self._icons)

    @property
    def i18n_middleware(self):
        """Middleware(I18nMiddleware): put it after the AuthenticationMiddleware."""
        return Middleware(I18nMiddleware, i18n=self.i18n)

    @property
    def lang(self):
        """The language of the current request, for <html lang="...">."""
        return self.i18n.lang

    @property
    def js_messages(self):
        """SWL's texts for swl.js, in the language of the current request."""
        return js_messages()

    @property
    def actions(self):
        return self._actions

    @property
    def styles(self):
        return self._web_resources.styles

    @property
    def scripts(self):
        return self._web_resources.scripts

    @property
    def globals(self):
        return dict(
            styles=self._web_resources.styles,
            scripts=self._web_resources.scripts,
        )

    @property
    def action_route(self):
        return Route(
            self._actions.actions_path,
            endpoint=self._actions.handle,
            methods=["GET", "POST"],
        )

    def register_modules(self, *args):
        self._actions.register_module(*args)

    def register_action_kwargs(self, **kwargs):
        for name, method in kwargs.items():
            if name != "swl":
                self._actions.register_kwarg(name, method)

    def register(self, *args, **kwargs):
        return self._actions.register(*args, **kwargs)

    def endpoint(self, *args, **kwargs):
        return self._actions.wrap(*args, **kwargs)

    def set_menu(self, title="", main=(), admin=(), user=(), **kwargs):
        """The menu for SWL's layouts (swl/layouts/*.j2): main (the menu), admin (a group
        of its own, "Manage"; admin_label= for another name) and user (the menu of the
        logged-in user), each a list of swl.menu.MenuItem. title is the app's name in the
        layout."""
        self.menu = Menu(title=title, main=main, admin=admin, user=user, **kwargs)

    def add_template_globals(self, **kwargs):
        for key, value in kwargs.items():
            if key not in ["SWL", "register"]:
                self._templates.env.globals[key] = value

    def add_template_filters(self, **kwargs):
        for key, value in kwargs.items():
            self._templates.env.filters[key] = value

    def success(self):
        return SuccessResponse(config=self._config.get("response", {}))

    def fail(self):
        return FailResponse()

    def template(self, name):
        return self._templates.get_template(name)

    def template_response(self, *args, **kwargs):
        return self._templates.TemplateResponse(*args, **kwargs)

    @property
    def password_managers_ignore(self):
        return Markup(
            " ".join(
                f'{name}="{escape(value[0])}"' if value else name
                for name, *value in [
                    ("data-1p-ignore",),
                    ("data-lpignore", "true"),
                    ("data-bwignore",),
                    ("data-form-type", "other"),
                    ("data-protonpass-ignore",),
                ]
            )
        )
