## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

import logging
from hashlib import md5

from starlette._exception_handler import wrap_app_handling_exceptions
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse

logger = logging.getLogger(__name__)


def hash_name(name):
    return md5(name.encode(encoding="utf-8")).hexdigest()


class Actions:
    def __init__(self, path="/action", default_auth=True, key=None):
        self._actions = {}
        self._path = path
        self._extra_kwargs = {}
        self._default_auth = default_auth
        self._key = key or hash_name
        if not self._path.startswith("/"):
            raise ValueError("path must start with /")

    @property
    def actions_path(self):
        return self._path + "/{action:str}"

    def register_module(self, *modules):
        for module in modules:
            if hasattr(module, "__actions__"):
                logger.info(
                    f"loading module {module.__name__}, "
                    + f"methods: {len(module.__actions__)}"
                )
                for item in module.__actions__:
                    if not isinstance(item, dict):
                        item = dict(method=item, authenticated=self._default_auth)
                    self.register_method(**item)

    def register_method(self, method, authenticated=None, is_authorized=None):
        if authenticated is None:
            authenticated = self._default_auth
        is_allowed = is_authorized_fn(authenticated, is_authorized)
        logger.debug(f"   - {method.__name__} - {is_allowed.__doc__}")

        key = self._key(method.__name__)
        self._actions[key] = dict(func=method, is_allowed=is_allowed)

    def register_kwarg(self, key, value):
        self._extra_kwargs[key] = value

    def register(self, method_name, path=None):
        key = self._key(method_name)
        if path is not None:
            return path + f"/{key}"
        if key not in self._actions:
            raise RuntimeError(f"Method not found: {method_name}")
        return self._path + f"/{key}"

    def get(self, key):
        return self._actions.get(key)

    def wrap(self, method, authenticated=True, **kwargs):
        return ActionMethodWrap(self, method, authenticated=authenticated, **kwargs)

    async def handle(self, request):
        if "action" in request.path_params:
            key = request.path_params["action"]
            if (action := self.get(key)) is None:
                raise HTTPException(404)
            logger.debug(f"handle {self._path}/{key[:8]}.. {action['func'].__name__}")

            user = request.user if "user" in request.scope else None
            if not await action["is_allowed"](user, request, **self._extra_kwargs):
                # action["authenticated"] is True and not request.user.is_authenticated:
                raise HTTPException(403)

            result = await action["func"](request, **self._extra_kwargs)
            return result
        raise HTTPException(404)


def is_authorized_fn(authenticated, is_authorized):
    doc = "authenticated=False"
    if authenticated:
        doc = "authenticated=True"
        if is_authorized is not None:
            doc += f", is_authorized={is_authorized.__name__}(...)"

    async def is_allowed(user, request, **kwargs):
        if not authenticated:
            return True
        if user is None or not user.is_authenticated:
            return False
        if is_authorized is not None:
            return await is_authorized(request, **kwargs)
        return True

    is_allowed.__doc__ = doc

    return is_allowed


class ActionMethodWrap:
    def __init__(
        self, actions, method, authenticated=True, is_authorized=None, redirect=None
    ):
        self._actions = actions
        self._method = method
        self._authenticated = authenticated
        self._is_authorized = is_authorized
        if is_authorized is not None and not authenticated:
            raise ValueError("is_authorized can only be set when authenticated is True")
        self.is_allowed = is_authorized_fn(authenticated, is_authorized)
        self._redirect = redirect

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive, send)

        if not await self.is_allowed(
            scope.get("user"), request, **self._actions._extra_kwargs
        ):
            if self._redirect is None:
                response = PlainTextResponse("Forbidden", status_code=403)
            else:
                request.session["next"] = request.url.path
                response = RedirectResponse(self._redirect, status_code=303)
            await response(scope, receive, send)
        else:

            async def app(scope, receive, send):
                response = await self._method(request, **self._actions._extra_kwargs)
                await response(scope, receive, send)

            await wrap_app_handling_exceptions(app, request)(scope, receive, send)
