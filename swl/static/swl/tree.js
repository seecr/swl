/* begin license *
 *
 * "SWL"(Seecr Web Lib) makes developing webbased apps easier
 *
 * Copyright (C) 2026 Seecr (Seek You Too B.V.) https://seecr.nl
 *
 * This file is part of "Seecr Web Lib"
 *
 * "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
 * SPDX-License-Identifier: MIT
 *
 * end license */

/*
 * Trees with jstree (https://www.jstree.com), driven by the server.
 *
 * Optional: a page that shows a tree loads this module
 *
 *     <script type="module" src="/static/swl/tree.js"></script>
 *
 * and jQuery, jstree and a jstree theme (jstree needs jQuery; SWL itself does not). See "Trees"
 * in doc/reference.md.
 *
 * The server drives the tree with swl.success().call(...):
 *
 *   tree_init     make the element with that id a tree; its nodes come from an action (data_url),
 *                 a click posts select_url, a drag and drop posts move_url
 *   tree_select   select a node
 *   tree_rename   change the text of a node
 *   tree_create   add nodes
 *   tree_delete   remove a node
 *   tree_refresh  load the nodes again (keeps what is open and selected)
 *
 * Every request posts `params` (given to tree_init) too, so an action knows which tree it is
 * about. Selecting a node from the server posts select_url as a click does, unless notify=false.
 */

import { swl_action, ui } from "./swl.js";

function _jquery() {
    let $ = window.jQuery;
    if (!$?.jstree) {
        console.error("SWL tree: jstree (and jQuery) is not loaded");
        ui.error("jstree is not loaded");
        return null;
    }
    return $;
}

/* "tree" or "#tree" */
function _elem(tree_id) {
    return document.getElementById(String(tree_id).replace(/^#/, ""));
}

function _tree(tree_id) {
    let $ = _jquery();
    let elem = _elem(tree_id);
    let tree = $ && elem ? $(elem).jstree(true) : false;
    if (!tree) {
        console.error("SWL tree: no tree " + tree_id);
    }
    return tree;
}

function _form_data(values) {
    let body = new FormData();
    for (let [key, value] of Object.entries(values)) {
        for (let each of Array.isArray(value) ? value : [value]) {
            if (each !== null && each !== undefined) {
                body.append(key, each);
            }
        }
    }
    return body;
}

/* The nodes from the data action: a list of jstree nodes (JSON), see swl.tree.tree_node. */
async function _load(url, values) {
    let response = await fetch(url, {method: "POST", body: _form_data(values), headers: {Accept: "application/json"}});
    if (response.redirected) {
        window.location.href = response.url;  // e.g. to the login page after the session expired
        return [];
    }
    if (!response.ok) {
        throw new Error("HTTP " + response.status);
    }
    return response.json();
}

/* Select one node (and open its parents). notify=false: without posting select_url. */
function _select(tree, node_id, notify = true) {
    tree._swl_quiet = !notify;
    try {
        tree.deselect_all(true);
        tree.select_node(node_id);
    } finally {
        tree._swl_quiet = false;
    }
    tree.get_node(node_id, true)?.[0]?.scrollIntoView?.({block: "nearest"});
}

/*
 * tree_id     id of the element (an empty element, or one with a <ul> when there is no data_url)
 * data_url    action that answers with the nodes as JSON; posted with node (the id of the node
 *             whose children are needed, "#" for the top) and selected. Without it jstree reads
 *             the <ul> inside the element.
 * select_url  action posted with node when a node is clicked (or selected from the server)
 * move_url    action posted with node, parent, position, old_parent and old_position after a
 *             drag and drop (positions count from 0 among the siblings, after the move). When
 *             the action fails, the tree reloads, so the node is back where the server has it.
 * params      values posted with every request
 * selected    the node to select when the tree is ready (with notify)
 * dnd         false (default), "same-parent" (only reorder within a parent) or "any"; a node
 *             with data: {draggable: false} cannot be dragged
 * types       jstree's types plugin: e.g. {"#": {valid_children: ["folder"]}, folder:
 *             {valid_children: ["item"]}, item: {valid_children: []}} limits where nodes can go
 * html        true: node texts are HTML; by default they are text (so a title with < is safe)
 * plugins, options   more jstree plugins and options, for what is not covered here
 */
function tree_init({tree_id, data_url = null, select_url = null, move_url = null, params = {},
                    selected = null, notify = true, dnd = false, types = null, html = false,
                    plugins = [], options = {}}) {
    let $ = _jquery();
    let elem = _elem(tree_id);
    if (!$ || !elem) {
        if (!elem) console.error("SWL tree: element not found: " + tree_id);
        return;
    }
    if ($(elem).jstree(true)) {
        if (!data_url) {
            return;  // a tree from the HTML in the element: that is gone, keep it as it is
        }
        $(elem).jstree("destroy");
    }

    let core = {
        multiple: false,
        force_text: !html,
        check_callback: (operation, node, parent) => {
            if (operation !== "move_node") {
                return true;  // create, rename, delete: done for the server
            }
            if (!dnd) {
                return false;
            }
            return dnd === "same-parent" ? parent.id === node.parent : true;
        },
        ...(options.core || {}),
    };
    if (data_url) {
        core.data = function (node, callback) {
            let tree = this;
            _load(data_url, {...params, node: node.id, selected: tree.get_selected()[0] ?? selected})
                .then((nodes) => callback.call(tree, nodes))
                .catch((error) => {
                    console.error("SWL tree: loading " + tree_id + " failed", error);
                    ui.error(String(error));
                    callback.call(tree, []);
                });
        };
    }
    let config = {...options, core: core, plugins: [...plugins]};
    if (dnd) {
        config.plugins.push("dnd");
        config.dnd = {
            is_draggable: (nodes) => nodes.every((node) => node.data?.draggable !== false),
            inside_pos: "last",
            ...(options.dnd || {}),
        };
    }
    if (types) {
        config.plugins.push("types");
        config.types = types;
    }

    $(elem)
        .on("ready.jstree", (e, data) => {
            if (selected) {
                _select(data.instance, selected, notify);
            }
        })
        .on("select_node.jstree", (e, data) => {
            if (select_url && !data.instance._swl_quiet) {
                swl_action(select_url, {...params, node: data.node.id});
            }
        })
        .on("move_node.jstree", async (e, data) => {
            if (!move_url) {
                return;
            }
            let ok = await swl_action(move_url, {
                ...params,
                node: data.node.id,
                parent: data.parent,
                position: data.position,
                old_parent: data.old_parent,
                old_position: data.old_position,
            });
            if (!ok) {
                data.instance.refresh();  // refused: show the tree as the server has it
            }
        })
        .jstree(config);
    elem.style.removeProperty("display");  // a tree is often hidden until it is ready
}

function tree_select({tree_id, node_id, notify = true}) {
    let tree = _tree(tree_id);
    if (tree) {
        _select(tree, node_id, notify);
    }
}

function tree_rename({tree_id, node_id, text}) {
    let tree = _tree(tree_id);
    if (tree) {
        tree.rename_node(node_id, text);
    }
}

/* nodes: [{id, text, parent, icon, ...}], each optionally with position (default "last") */
function tree_create({tree_id, nodes, select = null, notify = true}) {
    let tree = _tree(tree_id);
    if (!tree) {
        return;
    }
    for (let {position = "last", ...node} of nodes) {
        tree.create_node(node.parent ?? "#", node, position);
    }
    if (select) {
        _select(tree, select, notify);
    }
}

function tree_delete({tree_id, node_id, select = null, notify = true}) {
    let tree = _tree(tree_id);
    if (!tree) {
        return;
    }
    tree.delete_node(node_id);
    if (select) {
        _select(tree, select, notify);
    }
}

/* Load the nodes again; select: a node to select once that is done. */
function tree_refresh({tree_id, select = null, notify = true}) {
    let tree = _tree(tree_id);
    if (!tree) {
        return;
    }
    if (select) {
        window.jQuery(_elem(tree_id)).one("refresh.jstree", () => _select(tree, select, notify));
    }
    tree.refresh();
}

// The server calls these with swl.success().call("tree_...", ...): they must be global.
Object.assign(window, {tree_init, tree_select, tree_rename, tree_create, tree_delete, tree_refresh});

export { tree_init, tree_select, tree_rename, tree_create, tree_delete, tree_refresh };
