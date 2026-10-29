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

__all__ = ["SortInfo"]


class SortInfo:
    def __init__(self, columns):
        if isinstance(columns, str):
            columns = columns.split(",")
        self.columns = [SortInfo.Column(c) for c in columns]
        self.allowed = set(c.name for c in self.columns)

    @property
    def default_order(self):
        return ",".join(str(c) for c in self.columns)

    def sort(self, order):
        if order is None or not order.strip():
            order = self.default_order
        cols = [
            sc
            for sc in (SortInfo.Column(c) for c in order.split(","))
            if sc.name in self.allowed
        ]
        if not cols:
            return []

        result = []
        col0 = cols[0]
        result.append(
            {
                "column": col0.name,
                "reverse": col0.reverse,
                "next_order": ",".join(str(c) for c in [col0.reversed] + cols[1:]),
                "position": 0,
            }
        )
        for pos, col in enumerate(cols[1:], start=1):
            other_cols = [c for c in cols if c.name != col.name]
            result.append(
                {
                    "column": col.name,
                    "reverse": col.reverse,
                    "next_order": ",".join(str(c) for c in [col] + other_cols),
                    "position": pos,
                }
            )

        return result

    class Column:
        def __init__(self, column, reverse=None):
            if reverse is None:
                self.reverse = column.startswith("-")
                self.name = column[1:] if self.reverse else column
            else:
                self.reverse = reverse
                self.name = column

        def __str__(self):
            return f"{'-' if self.reverse else ''}{self.name}"

        @property
        def reversed(self):
            return self.__class__(self.name, not self.reverse)
