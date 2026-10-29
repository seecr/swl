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

__all__ = ["SessionSecretKey"]

import random
import string


class SessionSecretKey:
    def __init__(self, path):
        if path.exists():
            self.key = path.read_text().strip()
        else:
            self.key = "".join(
                random.choice(string.ascii_letters + string.digits) for _ in range(64)
            )
            path.write_text(self.key)
