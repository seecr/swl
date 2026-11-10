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

from datetime import date
from types import ModuleType

import pytest
from babel.messages.pofile import read_po
from babel.support import Translations
from seecr_stdlib.config import Config
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route, WebSocketRoute
from starlette.testclient import TestClient

from .i18n import (
    I18n,
    I18nMiddleware,
    _,
    accept_language,
    current_locale,
    format_date,
    locale_dir,
    ngettext,
)
from .swl import SWL
from .test_utils import assert_fail


def test_accept_language():
    assert accept_language("nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7") == [
        "nl-NL",
        "nl",
        "en-US",
        "en",
    ]
    assert accept_language("en;q=0.5, de, *;q=0.1, fr;q=0") == ["de", "en"]
    assert accept_language("") == []
    assert accept_language(None) == []


def test_match():
    i18n = I18n(locales=["en", "nl", "pt_BR"])
    assert i18n.default == "en"
    assert i18n.match("nl") == "nl"
    assert i18n.match("nl-BE") == "nl"
    assert i18n.match("NL_nl") == "nl"
    assert i18n.match("pt-BR") == "pt_BR"
    assert i18n.match("pt") == "pt_BR"
    assert i18n.match("de") is None
    assert i18n.match("nonsense!") is None
    assert i18n.match(None) is None
    with pytest.raises(ValueError):
        I18n(locales=["en", "klingon!"])


class Conn:
    def __init__(self, cookies=None, headers=None):
        self.cookies = cookies or {}
        self.headers = headers or {}


def test_select():
    i18n = I18n(locales=["en", "nl", "de"])
    assert i18n.select(Conn()) == "en"
    assert i18n.select(Conn(headers={"accept-language": "fr, de;q=0.8"})) == "de"
    both = Conn(cookies={"swl_lang": "nl"}, headers={"accept-language": "de"})
    assert i18n.select(both) == "nl"
    assert i18n.select(Conn(cookies={"swl_lang": "xx"})) == "en"
    i18n.locale_selector(lambda conn: "de")
    assert i18n.select(both) == "de"
    i18n.locale_selector(lambda conn: None)  # no preference: the rest decides
    assert i18n.select(both) == "nl"


def test_texts_outside_a_request_are_english():
    assert current_locale() is None
    assert _("Password incorrect") == "Password incorrect"
    assert _("Delete %(username)s", username="bob") == "Delete bob"
    assert ngettext("%(num)d user", "%(num)d users", 1) == "1 user"
    assert ngettext("%(num)d user", "%(num)d users", 3) == "3 users"


def test_activate():
    i18n = I18n(locales=["en", "nl"])
    token = i18n.activate("nl")
    try:
        assert current_locale() == "nl"
        assert _("Password incorrect") == "Wachtwoord onjuist"
        assert _("Delete %(username)s", username="bob") == "bob verwijderen"
        assert _("not translated") == "not translated"
        assert i18n.lang == "nl"
        assert format_date(date(2026, 11, 3), "long") == "3 november 2026"
    finally:
        i18n.deactivate(token)
    assert current_locale() is None


def test_application_catalogs_win(tmp_path):
    from babel.messages.catalog import Catalog
    from babel.messages.mofile import write_mo

    catalog = Catalog(locale="nl", domain="messages")
    catalog.add("Password incorrect", "Fout wachtwoord!")
    catalog.add("Hello", "Hallo")
    (tmp_path / "nl" / "LC_MESSAGES").mkdir(parents=True)
    with open(tmp_path / "nl" / "LC_MESSAGES" / "messages.mo", "wb") as f:
        write_mo(f, catalog)

    i18n = I18n(locales=["en", "nl"])
    i18n.add_translations(tmp_path)
    token = i18n.activate("nl")
    try:
        assert _("Hello") == "Hallo"
        assert _("Password incorrect") == "Fout wachtwoord!"
        assert _("Passwords do not match") == "De wachtwoorden zijn niet gelijk"
    finally:
        i18n.deactivate(token)


@pytest.mark.parametrize("language", ["nl", "de", "fr", "es"])
def test_swl_catalogs_are_complete_and_compiled(language):
    with open(locale_dir / "swl.pot", "rb") as f:
        template = read_po(f)
    with open(locale_dir / language / "LC_MESSAGES" / "swl.po", "rb") as f:
        catalog = read_po(f, locale=language)
    compiled = Translations.load(locale_dir, [language], "swl")
    for message in template:
        if not message.id:
            continue
        translated = catalog.get(message.id)
        assert translated is not None and translated.string, message.id
        if isinstance(message.id, str):
            # the .mo is compiled from the current .po
            assert compiled.gettext(message.id) == translated.string, message.id


def make_app(locales=("en", "nl")):
    swl = SWL(config=Config({"i18n": {"locales": list(locales)}}))

    views = ModuleType("views")

    async def fails(request, swl, **kwargs):
        return swl.fail().message(_("Password incorrect"))

    views.fails = fails
    views.__actions__ = [dict(method=fails, authenticated=False)]
    swl.register_modules(views)

    async def page(request, **kwargs):
        return swl.template_response(
            request, "swl/base.j2", {"title": "t", "body_class": "", "VERSION": "1"}
        )

    async def ws(websocket):
        await websocket.accept()
        await websocket.send_json({"locale": current_locale()})
        await websocket.close()

    app = Starlette(
        routes=[
            swl.action_route,
            Route("/", swl.endpoint(page, authenticated=False)),
            WebSocketRoute("/ws", ws),
        ],
        middleware=[swl.i18n_middleware],
    )
    return swl, TestClient(app)


def test_requests_get_their_language():
    swl, client = make_app()
    action = swl.register("fails")
    assert_fail(client.post(action), "Password incorrect")
    assert_fail(
        client.post(action, headers={"accept-language": "nl-NL,nl;q=0.9"}),
        "Wachtwoord onjuist",
    )
    client.cookies["swl_lang"] = "nl"
    assert_fail(client.post(action), "Wachtwoord onjuist")


def test_the_page_language():
    swl, client = make_app()
    page = client.get("/", headers={"accept-language": "nl"}).text
    assert '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="nl" lang="nl"' in page
    assert '"confirm": "Bevestigen"' in page  # swl.js texts
    assert '<span data-swl-lang-key="yes">Ja</span>' in page
    page = client.get("/").text
    assert 'lang="en"' in page and '"confirm": "Confirm"' in page


def test_websockets_get_their_language():
    swl, client = make_app()
    with client.websocket_connect("/ws", headers={"accept-language": "nl"}) as ws:
        assert ws.receive_json() == {"locale": "nl"}


def test_without_the_middleware_everything_is_english():
    swl = SWL(config=Config({"i18n": {"locales": ["nl", "en"]}}))
    template = swl._templates.env.from_string(
        '{{ _("Close") }} {% trans count=2 %}{{ count }} user{% pluralize %}'
        "{{ count }} users{% endtrans %}"
    )
    assert template.render() == "Close 2 users"
    token = swl.i18n.activate("nl")
    try:
        assert template.render() == "Sluiten 2 gebruikers"
    finally:
        swl.i18n.deactivate(token)


def test_i18n_tool(tmp_path):
    from .i18n_tool import main

    package = tmp_path / "app"
    (package / "templates").mkdir(parents=True)
    (package / "views.py").write_text('from swl.i18n import _\nMSG = _("Hello")\n')
    (package / "views_test.py").write_text('from swl.i18n import _\n_("Not this")\n')
    (package / "templates" / "page.j2").write_text('<p>{{ _("Goodbye") }}</p>')
    assert main(["extract", str(package)]) == 0
    pot = (package / "locale" / "messages.pot").read_text()
    assert 'msgid "Hello"' in pot and 'msgid "Goodbye"' in pot
    assert "Not this" not in pot

    main(["init", str(package), "nl"])
    po = package / "locale" / "nl" / "LC_MESSAGES" / "messages.po"
    text = po.read_text()
    po.write_text(text.replace('"Hello"\nmsgstr ""', '"Hello"\nmsgstr "Hallo"'))
    main(["compile", str(package)])
    i18n = I18n(locales=["en", "nl"])
    i18n.add_translations(package / "locale")
    token = i18n.activate("nl")
    try:
        assert _("Hello") == "Hallo"
    finally:
        i18n.deactivate(token)


def test_the_page_has_the_icons_for_swl_js():
    swl, client = make_app()
    page = client.get("/").text
    assert '<script type="application/json" id="swl-icons">' in page
    assert '"saved": "bi bi-check2"' in page
