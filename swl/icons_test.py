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

import pytest

from swl.icons import BOOTSTRAP_ICONS, icons


def test_default_bootstrap():
    assert icons() == BOOTSTRAP_ICONS
    assert icons()["close"] == "bi bi-x-lg"


def test_override_some():
    result = icons({"close": "ph-light ph-x"})
    assert result["close"] == "ph-light ph-x"
    assert result["confirm"] == BOOTSTRAP_ICONS["confirm"], "the others stay"
    assert BOOTSTRAP_ICONS["close"] == "bi bi-x-lg", "the defaults do not change"
    with pytest.raises(TypeError):
        result["close"] = "x"


def test_unknown_name():
    with pytest.raises(ValueError, match=r"Unknown icon names \['clsoe'\]"):
        icons({"clsoe": "ph-light ph-x"})


@pytest.mark.parametrize("classes", ["", "  ", None, 3])
def test_no_classes(classes):
    with pytest.raises(ValueError, match="'close': classes should be"):
        icons({"close": classes})
