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

from .tree import tree_node


def test_minimal():
    assert tree_node("a", "A") == {"id": "a", "text": "A"}


def test_flat():
    assert tree_node(1, "A", parent="#", icon="bi bi-folder", opened=True) == {
        "id": "1",
        "text": "A",
        "parent": "#",
        "icon": "bi bi-folder",
        "state": {"opened": True},
    }


def test_type_and_draggable():
    assert tree_node("a", "A", type="folder", draggable=False) == {
        "id": "a",
        "text": "A",
        "type": "folder",
        "data": {"draggable": False},
    }


def test_lazy_children_and_data():
    assert tree_node("a", "A", children=True, count=3) == {
        "id": "a",
        "text": "A",
        "children": True,
        "data": {"count": 3},
    }
