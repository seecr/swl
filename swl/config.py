## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2025 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

import logging
from copy import copy

color_end = "\033[0m"
color_red = "\033[1;31m"
color_yellow = "\033[1;33m"

colors = {
    "WARNING": color_yellow,
    "ERROR": color_red,
    "CRITICAL": color_red,
}


def colorize(levelname):
    if levelname in colors:
        return colors[levelname] + levelname + color_end
    return levelname


class DefaultFormatter(logging.Formatter):
    """
    A custom log formatter class.

    It does the following:
    * Outputs the LOG_LEVEL in uppercase, right-aligned to 8 characters

    Idea based on uvicorn.logging.DefaultFormatter
    """

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))
        recordcopy.__dict__["levelprefix"] = colorize(levelname) + ":" + seperator
        return super().formatMessage(recordcopy)


def configure_logging(loglevel):

    root = logging.getLogger()
    sh = logging.StreamHandler()
    df = DefaultFormatter("%(levelprefix)s %(message)s")
    sh.setFormatter(df)
    root.addHandler(sh)
    root.setLevel(loglevel)

    # set levels logging
    logging.getLogger("uvicorn").setLevel("INFO")
    logging.getLogger("python_multipart").setLevel("INFO")
    logging.getLogger("sqlalchemy.engine").setLevel("WARNING")
    logging.getLogger("aiosqlite").setLevel("WARNING")
    logging.getLogger("databases").setLevel("WARNING")
