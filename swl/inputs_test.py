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

"""The form field macros of swl/inputs.j2."""

import re

import pytest
from seecr_stdlib.config import Config

from .frameworks import FRAMEWORKS
from .swl import SWL


def render(source, framework="bootstrap", locales=None, **context):
    config = {"ui": {"framework": framework}}
    if locales:
        config["i18n"] = {"locales": locales}
    swl = SWL(config=Config(config))
    template = swl._templates.env.from_string(
        '{% from "swl/inputs.j2" import text_input, password_input, number_input, '
        "date_input, textarea_input, color_input %}" + source
    )
    return swl, template.render(**context)


def squash(html):
    return re.sub(r"\s+", " ", html).strip()


@pytest.mark.parametrize("framework", sorted(FRAMEWORKS))
def test_label_above_with_the_framework_classes(framework):
    _, html = render(
        '{{ text_input("Name", "name", value="Ann", id="f-name") }}', framework
    )
    html = squash(html)
    classes = FRAMEWORKS[framework].classes["input"]

    assert html.startswith('<div class="swl-field">')
    assert '<label for="f-name">Name</label>' in html
    assert (
        f'<input type="text" class="{classes}" id="f-name" name="name" value="Ann">'
        in html
    )
    assert html.index("<label") < html.index("<input"), "the label is above the control"
    assert "form-floating" not in html
    assert "placeholder" not in html


def test_every_macro():
    _, html = render(
        '{{ password_input("Password", "pw", id="a", autocomplete="new-password") }}'
        '{{ number_input("Age", "age", value=3, id="b") }}'
        '{{ date_input("Born", "born", value="2000-01-02", id="c") }}'
        '{{ textarea_input("Notes", "notes", value="x", height="4em", id="d") }}'
    )
    html = squash(html)
    assert (
        '<input type="password" class="form-control" id="a" name="pw"'
        ' autocomplete="new-password">' in html
    )
    password = html.split('id="a"')[1].split(">")[0]
    assert 'value="' not in password, "no password value"
    assert (
        '<input type="number" class="form-control" id="b" name="age" value="3">' in html
    )
    assert (
        'type="date" class="form-control" id="c" name="born" value="2000-01-02">'
        in html
    )
    assert (
        '<textarea class="form-control" id="d" name="notes" style="height: 4em">'
        "x</textarea>" in html
    )
    assert html.count('<div class="swl-field">') == 4


def test_mandatory_is_required():
    _, html = render(
        '{{ text_input("Name", "name", id="a", mandatory=True) }}'
        '{{ textarea_input("Notes", "notes", id="b", mandatory=True) }}'
        '{{ text_input("Other", "other", id="c") }}'
    )
    html = squash(html)
    assert 'id="a" name="name" value="" required>' in html
    assert 'id="b" name="notes" style="height: 2em" required>' in html
    assert 'id="c" name="other" value="">' in html


def test_optional():
    _, html = render('{{ text_input("Phone", "phone", id="a", optional=True) }}')
    assert (
        '<label for="a">Phone <span class="swl-optional">(optional)</span></label>'
        in squash(html)
    )

    _, html = render('{{ text_input("Phone", "phone", id="a") }}')
    assert "swl-optional" not in html


def test_optional_is_translated():
    swl, _ = render("", locales=["en", "nl"])
    token = swl.i18n.activate("nl")
    try:
        html = swl._templates.env.from_string(
            '{% from "swl/inputs.j2" import text_input %}'
            '{{ text_input("Telefoon", "phone", id="a", optional=True) }}'
        ).render()
    finally:
        swl.i18n.deactivate(token)
    assert '<span class="swl-optional">(optioneel)</span>' in html


def test_hint():
    _, html = render(
        '{{ text_input("Name", "name", id="a", hint="As in your passport") }}'
    )
    html = squash(html)
    assert 'aria-describedby="a-hint"' in html
    assert '<div class="swl-hint" id="a-hint">As in your passport</div>' in html
    assert html.index("<input") < html.index("swl-hint"), "below the control"


def test_form_and_escaping():
    _, html = render(
        '{{ text_input(label, "name", value=value, form="f1", id="a") }}',
        label="<b>Name</b>",
        value='"><script>',
    )
    assert 'form="f1"' in html
    assert "<script>" not in html and "<b>" not in html
    assert "&lt;b&gt;Name&lt;/b&gt;" in html


def test_random_ids_link_label_and_control():
    _, html = render('{{ text_input("Name", "name") }}')
    (label_for,) = re.findall(r'<label for="([0-9a-f]{10})"', html)
    assert f'id="{label_for}"' in html


def test_color_input():
    _, html = render('{{ color_input("Colour", "color", value="#1C7ED6", id="c") }}')
    html = squash(html)
    assert '<label for="c">Colour</label>' in html
    assert '<input type="hidden" name="color" value="#1c7ed6">' in html, "lower case"
    assert (
        '<button type="button" class="swl-color-button" id="c"'
        ' popovertarget="c-colors"' in html
    )
    assert '<span class="swl-color-value">#1c7ed6</span>' in html
    assert '<div class="swl-color-panel" id="c-colors" popover>' in html
    swatches = re.findall(r'data-swl-color="(#[0-9a-f]{6})"', html)
    assert len(swatches) == 18
    assert swatches[-2:] == ["#000000", "#ffffff"]
    assert len(set(swatches)) == 18
    assert html.count('aria-pressed="true"') == 1
    assert (
        'data-swl-color="#1c7ed6" style="background-color: #1c7ed6" title="Blue"' in html
    )
    assert html.count('type="number" class="form-control" min="0" max="255"') == 3
    assert "Custom colour" in html
    assert "swl-color-clear" not in html, "not optional: no 'No colour'"


def test_color_input_clear():
    _, html = render('{{ color_input("Colour", "color", id="c", optional=True) }}')
    html = squash(html)
    assert (
        '<button type="button" class="swl-color-clear" aria-pressed="true">'
        ' <span class="swl-color-sample"></span>No colour </button>' in html
    )
    _, html = render(
        '{{ color_input("Colour", "color", value="#000000", optional=True) }}'
    )
    assert 'class="swl-color-clear" aria-pressed="false"' in html
    _, html = render('{{ color_input("Colour", "color", optional=True, clear=False) }}')
    assert "swl-color-clear" not in html
    _, html = render('{{ color_input("Colour", "color", clear=True) }}')
    assert "swl-color-clear" in html and "swl-optional" not in html


def test_color_input_own_colors_no_custom():
    _, html = render(
        '{{ color_input("Colour", "color", colors=["#ff0000", ("#00ff00", "Grass")],'
        ' custom=False, id="c", form="f1") }}'
    )
    html = squash(html)
    assert re.findall(r'data-swl-color="([^"]*)"', html) == ["#ff0000", "#00ff00"]
    assert 'title="#ff0000"' in html and 'title="Grass"' in html
    assert "swl-color-custom" not in html
    assert '<input type="hidden" name="color" value="" form="f1">' in html
    assert 'aria-pressed="true"' not in html


@pytest.mark.parametrize(
    "value", ["red", "#fff", "#12345g", 'x" onclick="evil', "#123456; color: red", None]
)
def test_color_input_only_takes_a_colour(value):
    _, html = render(
        '{{ color_input("Colour", "color", value=value, colors=[value or "x"],'
        ' id="c") }}',
        value=value,
    )
    assert '<input type="hidden" name="color" value="">' in html
    assert "data-swl-color" not in html
    assert "evil" not in html and "color: red" not in html


def test_color_input_translated():
    swl, _ = render("", locales=["en", "nl"])
    token = swl.i18n.activate("nl")
    try:
        html = swl._templates.env.from_string(
            '{% from "swl/inputs.j2" import color_input %}'
            '{{ color_input("Kleur", "color", id="c") }}'
        ).render()
    finally:
        swl.i18n.deactivate(token)
    assert 'title="Rood"' in html
    assert "Eigen kleur" in html
