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
Translation catalogs for SWL and SWL applications, with Babel.

    python -m swl.i18n_tool extract <package>            # texts -> locale/<domain>.pot
    python -m swl.i18n_tool init <package> <language>    # a new .po for a language
    python -m swl.i18n_tool update <package>             # .pot -> every .po
    python -m swl.i18n_tool compile <package>            # .po -> .mo (what is used)

<package> is the directory of the Python package (e.g. "myapp"); the catalogs go to
<package>/locale; --domain is "messages" (SWL's own: "swl"). Texts are found in *.py
(_, N_, gettext, ngettext) and in templates *.j2 ({{ _("...") }}, {% trans %}); tests
(*_test.py) are skipped. Commit the .po and the .mo files.
"""

import argparse
import sys
import tempfile
from pathlib import Path

from babel.messages.frontend import CommandLineInterface

MAPPING = """\
[ignore: **/*_test.py]
[ignore: **/env/**]
[python: **.py]
[jinja2: **.j2]
trim_blocks = true
lstrip_blocks = true
"""


def run(*args):
    CommandLineInterface().run(["pybabel", "-q", *args])


def extract(package, domain, locale_dir):
    locale_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".cfg") as mapping:
        mapping.write(MAPPING)
        mapping.flush()
        run(
            "extract",
            "-F", mapping.name,
            "-k", "N_",
            "-k", "ngettext:1,2",
            "--sort-by-file",
            "--project", package.name,
            "-o", str(locale_dir / f"{domain}.pot"),
            str(package),
        )  # fmt: skip


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m swl.i18n_tool")
    parser.add_argument("command", choices=["extract", "init", "update", "compile"])
    parser.add_argument("package", type=Path, help="the package directory")
    parser.add_argument("language", nargs="?", help="for init, e.g. nl")
    parser.add_argument("--domain", default="messages")
    args = parser.parse_args(argv)

    locale_dir = args.package / "locale"
    pot = locale_dir / f"{args.domain}.pot"
    if args.command == "extract":
        extract(args.package, args.domain, locale_dir)
    elif args.command == "init":
        if not args.language:
            parser.error("init needs a language, e.g. nl")
        run("init", "-i", str(pot), "-d", str(locale_dir), "-D", args.domain,
            "-l", args.language)  # fmt: skip
    elif args.command == "update":
        run("update", "-i", str(pot), "-d", str(locale_dir), "-D", args.domain,
            "--ignore-obsolete")  # fmt: skip
    elif args.command == "compile":
        run("compile", "-d", str(locale_dir), "-D", args.domain)
    return 0


if __name__ == "__main__":
    sys.exit(main())
