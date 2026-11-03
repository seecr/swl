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

"""The help balloon of swl/info.j2."""

import re

from markupsafe import Markup
from seecr_stdlib.config import Config

from .swl import SWL


def render(source, locales=None, **context):
    config = {"ui": {"framework": "bootstrap"}}
    if locales:
        config["i18n"] = {"locales": locales}
    swl = SWL(config=Config(config))
    template = swl._templates.env.from_string(
        '{% from "swl/info.j2" import info %}' + source
    )
    return swl, template.render(**context)


def test_a_button_and_its_balloon():
    _, html = render('{{ info("Shown in the top bar") }}')
    match = re.fullmatch(r"(<button.*?</button>)\s*(<span.*</span>)", html)
    button, balloon = match.groups()
    target = re.search(r'popovertarget="(swl-info-[0-9a-f]{10})"', button).group(1)
    assert 'type="button"' in button and 'class="swl-info"' in button
    assert 'aria-label="More information"' in button
    assert balloon == (
        f'<span id="{target}" class="swl-info-text" popover>Shown in the top bar</span>'
    )


def test_every_balloon_has_its_own_id():
    _, html = render('{{ info("one") }}{{ info("two") }}')
    ids = re.findall(r'popovertarget="([^"]+)"', html)
    assert len(set(ids)) == 2


def test_text_is_escaped_unless_markup():
    _, html = render("{{ info(text) }}", text="<b>bold</b> & more")
    assert "&lt;b&gt;bold&lt;/b&gt; &amp; more" in html
    _, html = render("{{ info(text) }}", text=Markup("<b>bold</b>"))
    assert "<b>bold</b>" in html


def test_own_label():
    _, html = render('{{ info("text", label="About colours") }}')
    assert 'aria-label="About colours"' in html


def test_label_is_translated():
    swl, _ = render("", locales=["en", "nl"])
    token = swl.i18n.activate("nl")
    try:
        html = swl._templates.env.from_string(
            '{% from "swl/info.j2" import info %}{{ info("tekst") }}'
        ).render()
    finally:
        swl.i18n.deactivate(token)
    assert 'aria-label="Meer informatie"' in html
