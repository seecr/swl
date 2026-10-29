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

import asyncio
import signal

__all__ = ["Shutdown"]


class Shutdown:
    def __init__(self):
        self._event = asyncio.Event()
        self._callbacks = []

        loop = asyncio.get_event_loop()
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, self._shutdown)

    def add_callback(self, f):
        self._callbacks.append(f)

    def _shutdown(self):
        print("Starting shutdown", flush=True)
        for callback in self._callbacks:
            callback()
        self._event.set()
        print("Completed shutdown", flush=True)

    async def wait(self):
        await self._event.wait()
