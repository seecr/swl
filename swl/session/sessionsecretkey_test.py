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

from .sessionsecretkey import SessionSecretKey


def test_key(tmp_path):
    path = tmp_path / "session_secret_key.txt"
    key = SessionSecretKey(path).key
    assert len(key) == 64

    again = SessionSecretKey(path).key
    assert key == again
