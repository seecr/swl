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

from .info import SortInfo


def test_sortinfo():
    info = SortInfo(["A", "B", "C"])
    assert info.default_order == "A,B,C"
    assert [str(c) for c in info.columns] == ["A", "B", "C"]

    assert info.sort("A,B,C") == [
        {"column": "A", "reverse": False, "next_order": "-A,B,C", "position": 0},
        {"column": "B", "reverse": False, "next_order": "B,A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,A,B", "position": 2},
    ]

    assert info.sort("-A,B,C") == [
        {"column": "A", "reverse": True, "next_order": "A,B,C", "position": 0},
        {"column": "B", "reverse": False, "next_order": "B,-A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-A,B", "position": 2},
    ]
    assert info.sort("-A,-B,C") == [
        {"column": "A", "reverse": True, "next_order": "A,-B,C", "position": 0},
        {"column": "B", "reverse": True, "next_order": "-B,-A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-A,-B", "position": 2},
    ]
    assert info.sort("-B,-A,C") == [
        {"column": "B", "reverse": True, "next_order": "B,-A,C", "position": 0},
        {"column": "A", "reverse": True, "next_order": "-A,-B,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-B,-A", "position": 2},
    ]


def test_sort_unknown():
    info = SortInfo(["A", "B", "C"])
    assert info.sort("D") == []
    assert info.sort("D,A") == [
        {"column": "A", "reverse": False, "next_order": "-A", "position": 0}
    ]


def test_default_order():
    info = SortInfo(["-A", "B", "C"])
    assert info.default_order == "-A,B,C"
    assert [str(c) for c in info.columns] == ["-A", "B", "C"]


def test_other_input():
    info = SortInfo("-A,B,C")
    assert info.default_order == "-A,B,C"
    assert [str(c) for c in info.columns] == ["-A", "B", "C"]


def test_sort_empty_arg():
    info = SortInfo("-A,B,C")
    assert info.sort(None) == [
        {"column": "A", "reverse": True, "next_order": "A,B,C", "position": 0},
        {"column": "B", "reverse": False, "next_order": "B,-A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-A,B", "position": 2},
    ]
    assert info.sort("") == [
        {"column": "A", "reverse": True, "next_order": "A,B,C", "position": 0},
        {"column": "B", "reverse": False, "next_order": "B,-A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-A,B", "position": 2},
    ]
    assert info.sort("\t   ") == [
        {"column": "A", "reverse": True, "next_order": "A,B,C", "position": 0},
        {"column": "B", "reverse": False, "next_order": "B,-A,C", "position": 1},
        {"column": "C", "reverse": False, "next_order": "C,-A,B", "position": 2},
    ]
