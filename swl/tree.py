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

"""
The server side of trees (static/swl/tree.js, jstree): the nodes a data action answers
with.

    from starlette.responses import JSONResponse
    from swl.tree import tree_node

    async def folder_tree_data(request, swl, **kwargs):
        return JSONResponse([
            tree_node("f1", "Documents", parent="#", icon="bi bi-folder", opened=True),
            tree_node("d1", "Letter", parent="f1", icon="bi bi-file-text"),
        ])

See "Trees" in doc/reference.md.
"""

__all__ = ["tree_node"]


def tree_node(
    id,
    text,
    parent=None,
    icon=None,
    opened=False,
    type=None,
    draggable=True,
    children=None,
    **data,
):
    """A jstree node.

    parent: the id of its parent, "#" for the top. Give it to every node when the
        action answers with all nodes at once (a flat list); leave it out when it answers
        with the children of one node (lazy loading, tree.js posts that node's id as
        "node").
    icon: CSS classes, e.g. "bi bi-folder".
    opened: show its children.
    type: for the types option of tree_init (where a node may be dropped).
    draggable: False: this node cannot be dragged.
    children: True: it has children that load when it is opened (lazy loading); or a
        list of nodes.
    data: anything else, kept with the node in the browser (node.data).
    """
    node = {"id": str(id), "text": text}
    if parent is not None:
        node["parent"] = str(parent)
    if icon:
        node["icon"] = icon
    if opened:
        node["state"] = {"opened": True}
    if type is not None:
        node["type"] = type
    if children is not None:
        node["children"] = children
    if not draggable:
        data["draggable"] = False
    if data:
        node["data"] = data
    return node
