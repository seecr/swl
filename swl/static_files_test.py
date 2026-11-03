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

import os

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from . import StaticFiles, static_dir


def client(**kwargs):
    return TestClient(Starlette(routes=[Mount("/static", StaticFiles(**kwargs))]))


def test_the_browser_always_checks_with_the_server(tmp_path):
    (tmp_path / "app.js").write_text("one()")
    c = client(directory=tmp_path)

    response = c.get("/static/app.js")
    assert response.status_code == 200
    assert response.text == "one()"
    assert response.headers["cache-control"] == "no-cache"
    etag = response.headers["etag"]
    assert response.headers["last-modified"]

    # unchanged: a 304 without the file, still no-cache
    response = c.get("/static/app.js", headers={"if-none-match": etag})
    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["cache-control"] == "no-cache"

    # changed: the new file
    (tmp_path / "app.js").write_text("two(); // changed")
    stat = (tmp_path / "app.js").stat()
    os.utime(tmp_path / "app.js", (stat.st_atime, stat.st_mtime + 10))
    response = c.get("/static/app.js", headers={"if-none-match": etag})
    assert response.status_code == 200
    assert response.text == "two(); // changed"
    assert response.headers["etag"] != etag


def test_swls_own_files_and_packages():
    response = client(directory=static_dir).get("/static/swl/swl.js")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"

    # as an application mounts its own files with SWL's
    response = client(packages=[("swl", "static")]).get("/static/swl/swl-run.js")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


def test_not_found(tmp_path):
    response = client(directory=tmp_path).get("/static/nope.js")
    assert response.status_code == 404


def test_other_cache_control(tmp_path):
    (tmp_path / "app.js").write_text("x")
    immutable = "public, max-age=31536000, immutable"
    response = client(directory=tmp_path, cache_control=immutable).get("/static/app.js")
    assert response.headers["cache-control"] == immutable

    response = client(directory=tmp_path, cache_control=None).get("/static/app.js")
    assert "cache-control" not in response.headers, "None: as Starlette's"
