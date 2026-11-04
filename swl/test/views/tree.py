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

"""Actions for js-test/tree.test.js (static/swl/tree.js). Each answers with a call to
tree_test_record, so the test sees what was posted."""

from starlette.responses import JSONResponse

from swl.responses import FailResponse, SuccessResponse
from swl.tree import tree_node

# what tree_test_data answers; the test changes it with tree_test_set_nodes
NODES = []


def _posted(form):
    return {k: v for k, v in sorted(form.multi_items())}


async def tree_test_data(request, **kwargs):
    async with request.form() as form:
        posted = _posted(form)
    nodes = [dict(n) for n in NODES] or [
        tree_node("f1", "Folder <b>1</b>", parent="#", opened=True, type="folder",
                  draggable=False),
        tree_node("a", "A", parent="f1", type="item"),
        tree_node("b", "B", parent="f1", type="item"),
        tree_node("c", "C", parent="f1", type="item"),
        tree_node("f2", "Folder 2", parent="#", opened=True, type="folder",
                  draggable=False),
        tree_node("d", "D", parent="f2", type="item"),
    ]
    # the posted values travel along with the first node, for the test to check
    nodes[0].setdefault("data", {})["posted"] = posted
    return JSONResponse(nodes)


async def tree_test_set_nodes(request, **kwargs):
    async with request.form() as form:
        NODES[:] = [
            tree_node(id, id.upper(), parent="#") for id in form.getlist("id")
        ]
    return SuccessResponse()


async def tree_test_select(request, **kwargs):
    async with request.form() as form:
        posted = _posted(form)
    return SuccessResponse().call("tree_test_record", action="select", **posted)


async def tree_test_move(request, **kwargs):
    async with request.form() as form:
        posted = _posted(form)
    if posted["node"] == "c":
        return FailResponse().message("C stays where it is")
    return SuccessResponse().call("tree_test_record", action="move", **posted)


async def tree_test_fail(request, **kwargs):
    return FailResponse().message("No")


__actions__ = [
    dict(authenticated=False, method=tree_test_data),
    dict(authenticated=False, method=tree_test_set_nodes),
    dict(authenticated=False, method=tree_test_select),
    dict(authenticated=False, method=tree_test_move),
    dict(authenticated=False, method=tree_test_fail),
]
