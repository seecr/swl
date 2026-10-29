## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##


class Crumb:
    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)

    def __init__(self, label, action, arguments):
        self.label = label
        self.action = action
        self.arguments = arguments

    def __eq__(self, other):
        return (
            self.label == other.label
            and self.action == other.action
            and self.arguments == other.arguments
        )

    def as_dict(self):
        return dict(label=self.label, action=self.action, arguments=self.arguments)


class Breadcrumbs:
    def __init__(self, breadcrumbs):
        self._crumbs = [Crumb.from_dict(crumb) for crumb in (breadcrumbs or [])]

    def add(self, label, action, arguments=None):
        new_crumb = Crumb(label=label, action=action, arguments=arguments or {})

        if new_crumb in self._crumbs:
            self._crumbs = self._crumbs[: self._crumbs.index(new_crumb) + 1]
        else:
            self._crumbs.append(new_crumb)

    def __iter__(self):
        return iter(self._crumbs)

    def as_dict(self):
        return [crumb.as_dict() for crumb in self._crumbs]
