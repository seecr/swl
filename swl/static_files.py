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

"""Static files that are never stale in the browser.

Starlette's StaticFiles sends no Cache-Control. A browser then guesses how long it may
use its copy without asking ("heuristic freshness", often days), so after an update it
can keep running the old swl.js or app.js against new html. A version in the url does
not help for JavaScript modules: swl-run.js?version=2 still imports "./swl.js" without
it.

This StaticFiles sends "Cache-Control: no-cache": the browser keeps the file, but asks the
server before every use whether it changed. The ETag (and Last-Modified) that StaticFiles
already sends make that a cheap 304 Not Modified when it did not.

    from swl import StaticFiles, static_dir
    Mount("/static", StaticFiles(directory=static_dir))
"""

from starlette.staticfiles import StaticFiles as _StarletteStaticFiles

NO_CACHE = "no-cache"


class StaticFiles(_StarletteStaticFiles):
    """Starlette's StaticFiles (same arguments), with Cache-Control on every file.

    cache_control: the header; "no-cache" (default) makes the browser check every time.
    Use e.g. "public, max-age=31536000, immutable" only for urls that change with
    their content."""

    def __init__(self, *args, cache_control=NO_CACHE, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_control = cache_control

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        if self.cache_control:
            # also on a 304: it keeps the copy in the browser "no-cache"
            response.headers["cache-control"] = self.cache_control
        return response
