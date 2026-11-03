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

import logging

import pytest

from .config import configure_logging

QUIETED = {
    "uvicorn": logging.INFO,
    "python_multipart": logging.INFO,
    "sqlalchemy.engine": logging.WARNING,
    "aiosqlite": logging.WARNING,
    "databases": logging.WARNING,
    "PIL": logging.INFO,  # Pillow logs every chunk of every image it reads at DEBUG
}


@pytest.fixture
def restore_logging():
    """configure_logging changes global state: the levels and the root's handlers."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    levels = {name: logging.getLogger(name).level for name in QUIETED}
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, saved in levels.items():
        logging.getLogger(name).setLevel(saved)


def test_configure_logging(restore_logging):
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG
    assert logging.getLogger("my_app").isEnabledFor(logging.DEBUG), "the application's own"
    for name, level in QUIETED.items():
        assert logging.getLogger(name).level == level, name
    assert not logging.getLogger("PIL.PngImagePlugin").isEnabledFor(logging.DEBUG)
