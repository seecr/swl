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

"""
Translations (gettext, with Babel) and dates and numbers in the visitor's language.

Texts are written in English and marked for translation:

    from swl.i18n import _, ngettext
    swl.fail().message(_("Passwords do not match"))
    _("Hello %(name)s", name=user.name)
    ngettext("%(num)d user", "%(num)d users", len(users))

and in templates (jinja2.ext.i18n, "newstyle"):

    {{ _("Users") }}  {{ _("Delete %(name)s?", name=user.name) }}
    {% trans count=users|length %}{{ count }} user{% pluralize %}{{ count }} users
    {% endtrans %}

The language is chosen per request (and per websocket) by I18nMiddleware:
  1. the application's selector, e.g. the language in the user's profile
     (swl.i18n.locale_selector(fn), fn(conn) -> "nl" or None);
  2. the cookie "swl_lang", e.g. for a language switch;
  3. the browser's Accept-Language;
  4. the first of "i18n.locales" in the config (default ["en"]).
Only the languages in "i18n.locales" are used. Without the middleware everything is in
English, as the texts are written.

SWL's own texts are in swl/locale (domain "swl"); an application adds its catalogs with
swl.i18n.add_translations(path) (domain "messages" by default); they win over SWL's.
`python -m swl.i18n_tool` extracts texts and compiles catalogs.
"""

import contextvars
from pathlib import Path

from babel import Locale, UnknownLocaleError, dates, numbers
from babel.support import NullTranslations, Translations
from starlette.requests import HTTPConnection

locale_dir = Path(__file__).parent / "locale"
DOMAIN = "swl"
COOKIE = "swl_lang"

_current = contextvars.ContextVar("swl_locale", default=None)  # (locale, translations)


def N_(message):
    """Marks a text for translation without translating it (yet)."""
    return message


def _format(text, variables):
    return text % variables if variables else text


def _(message, **variables):
    """The message in the language of the current request."""
    current = _current.get()
    text = current[1].gettext(message) if current else message
    return _format(text, variables)


gettext = _


def ngettext(singular, plural, num, **variables):
    """Singular or plural, in the language of the current request; %(num)d is num."""
    current = _current.get()
    if current:
        text = current[1].ngettext(singular, plural, num)
    else:
        text = singular if num == 1 else plural
    variables.setdefault("num", num)
    return _format(text, variables)


def current_locale():
    """The locale of the current request (a string such as "nl" or "pt_BR"), or None
    outside a request (or without I18nMiddleware)."""
    current = _current.get()
    return current[0] if current else None


def _parse(tag):
    """A language tag ("nl-NL", "nl_nl", "NL") as a babel Locale, or None."""
    if not tag or not isinstance(tag, str):
        return None
    try:
        return Locale.parse(tag.strip().replace("-", "_"))
    except (ValueError, UnknownLocaleError):
        return None


def accept_language(header):
    """The language tags in an Accept-Language header, the preferred one first."""
    tags = []
    for nr, part in enumerate((header or "").split(",")):
        tag, _sep, params = part.strip().partition(";")
        if not tag or tag == "*":
            continue
        quality = 1.0
        for param in params.split(";"):
            name, _eq, value = param.strip().partition("=")
            if name == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        if quality > 0:
            tags.append((-quality, nr, tag.strip()))
    return [tag for *_order, tag in sorted(tags)]


class I18n:
    def __init__(self, locales=None, cookie=COOKIE):
        parsed = [_parse(tag) for tag in (locales or ["en"])]
        if None in parsed:
            raise ValueError(f"Unknown locale in i18n.locales: {locales!r}")
        self.locales = [str(locale) for locale in parsed]
        self.default = self.locales[0]
        self.cookie = cookie
        self._catalogs = [(locale_dir, DOMAIN)]
        self._translations = {}
        self._selector = None

    def add_translations(self, path, domain="messages"):
        """The application's catalogs: <path>/<locale>/LC_MESSAGES/<domain>.mo."""
        self._catalogs.append((Path(path), domain))
        self._translations.clear()

    def locale_selector(self, fn):
        """fn(conn) -> a language tag or None; conn is the request or websocket, after
        the AuthenticationMiddleware (conn.user). Can be used as a decorator."""
        self._selector = fn
        return fn

    def translations(self, locale):
        if locale not in self._translations:
            merged = NullTranslations()
            for path, domain in self._catalogs:
                found = Translations.load(path, [locale], domain)
                if isinstance(found, Translations):
                    if isinstance(merged, Translations):
                        merged.merge(found)  # later catalogs win
                    else:
                        merged = found
            self._translations[locale] = merged
        return self._translations[locale]

    def match(self, tag):
        """The supported locale for a language tag (also "nl_BE" -> "nl"), or None."""
        locale = _parse(tag)
        if locale is None:
            return None
        if str(locale) in self.locales:
            return str(locale)
        for supported in self.locales:
            if Locale.parse(supported).language == locale.language:
                return supported
        return None

    def select(self, conn):
        """The locale for a request or websocket."""
        if self._selector is not None and (found := self.match(self._selector(conn))):
            return found
        if found := self.match(conn.cookies.get(self.cookie)):
            return found
        for tag in accept_language(conn.headers.get("accept-language")):
            if found := self.match(tag):
                return found
        return self.default

    def activate(self, locale):
        """Use this locale in the current context (as the middleware does); returns a
        token for deactivate(). For tests and background jobs."""
        locale = self.match(locale) or self.default
        return _current.set((locale, self.translations(locale)))

    @staticmethod
    def deactivate(token):
        _current.reset(token)

    # for templates

    @property
    def lang(self):
        """The current language as an HTML lang value ("nl", "pt-BR"); "en" outside a
        request, like the texts."""
        return (current_locale() or "en").replace("_", "-")


class I18nMiddleware:
    """
    Chooses the language for every request and websocket (see the module). Put it after
    the AuthenticationMiddleware, so a selector can look at the user:

        middleware=[..., Middleware(AuthenticationMiddleware, ...), swl.i18n_middleware]
    """

    def __init__(self, app, i18n):
        self.app = app
        self.i18n = i18n

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        token = self.i18n.activate(self.i18n.select(HTTPConnection(scope)))
        try:
            await self.app(scope, receive, send)
        finally:
            I18n.deactivate(token)


# dates and numbers, in the current language


def _locale():
    return current_locale() or "en"


def format_date(value, format="medium"):
    return dates.format_date(value, format=format, locale=_locale())


def format_time(value, format="short", tzinfo=None):
    return dates.format_time(value, format=format, tzinfo=tzinfo, locale=_locale())


def format_datetime(value, format="medium", tzinfo=None):
    return dates.format_datetime(value, format=format, tzinfo=tzinfo, locale=_locale())


def format_skeleton(value, skeleton, tzinfo=None):
    """A date in a flexible format: "MMMEd" -> "Mon, Nov 3" / "ma 3 nov"."""
    return dates.format_skeleton(skeleton, value, tzinfo=tzinfo, locale=_locale())


def format_number(value):
    return numbers.format_decimal(value, locale=_locale())


def format_timedelta(value, **kwargs):
    return dates.format_timedelta(value, locale=_locale(), **kwargs)


TEMPLATE_FILTERS = dict(
    format_date=format_date,
    format_time=format_time,
    format_datetime=format_datetime,
    format_skeleton=format_skeleton,
    format_number=format_number,
    format_timedelta=format_timedelta,
)


def install(env, i18n):
    """Jinja: {{ _("...") }}, {% trans %}, and the format_* filters."""
    env.add_extension("jinja2.ext.i18n")

    def gettext(message):
        current = _current.get()
        return current[1].gettext(message) if current else message

    def ngettext_(singular, plural, num):
        current = _current.get()
        if current:
            return current[1].ngettext(singular, plural, num)
        return singular if num == 1 else plural

    env.install_gettext_callables(gettext=gettext, ngettext=ngettext_, newstyle=True)
    env.filters.update(TEMPLATE_FILTERS)


# The texts swl.js shows (lang.js: _get(key)); base.j2 puts them in the page.
JS_MESSAGES = {
    "confirm": N_("Confirm"),
    "yes": N_("Yes"),
    "no": N_("No"),
    "ok": N_("Ok"),
    "error": N_("Error"),
    "info": N_("Info"),
    "error_server": N_("The server could not process the request"),
    "error_network": N_("The server could not be reached"),
    "error_forbidden": N_("You are not allowed to do this, or your session has expired"),
    "error_not_found": N_("The requested action does not exist"),
    "error_invalid_response": N_("The server sent an unexpected response"),
    "error_unknown_function": N_("Unknown function"),
    "error_function_failed": N_("Error in function"),
    "saved": N_("Saved"),
}


def js_messages():
    return {key: _(message) for key, message in JS_MESSAGES.items()}


__all__ = [
    "_",
    "N_",
    "gettext",
    "ngettext",
    "current_locale",
    "I18n",
    "I18nMiddleware",
]
