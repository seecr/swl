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
 * Trees (static/swl/tree.js, jstree). The actions are in swl/test/views/tree.py; they answer
 * with a call to tree_test_record, so a test sees what was posted.
 */

import { swl_action } from "/static/swl/swl.js";
import "/static/swl/tree.js";

const DATA = "/action/tree_test_data";
const SELECT = "/action/tree_test_select";
const MOVE = "/action/tree_test_move";

let recorded = [];

function waitFor(condition, what = "condition", timeout = 3000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        (function poll() {
            if (condition()) {
                return resolve();
            }
            if (Date.now() - start > timeout) {
                return reject(new Error(`timeout waiting for ${what}; recorded=${JSON.stringify(recorded)}`));
            }
            setTimeout(poll, 20);
        })();
    });
}

const pause = (ms = 150) => new Promise((resolve) => setTimeout(resolve, ms));
const tree = () => window.jQuery("#the_tree").jstree(true);
const children = (id) => tree().get_node(id).children;
const selected = () => tree().get_selected();

/* tree_init on #the_tree; resolves when its nodes are there */
async function init(options = {}) {
    window.tree_init({tree_id: "#the_tree", data_url: DATA, select_url: SELECT, move_url: MOVE, ...options});
    // after tree_init: it removes the handlers of a tree it replaces. Loading takes a request,
    // so ready comes later (a tree from HTML is ready at once).
    if (!tree()?.get_node("#")?.state?.loaded) {
        await new Promise((resolve) => window.jQuery("#the_tree").one("ready.jstree", resolve));
    }
    await pause(20);  // the ready handler (selected) runs after the event
}

const DIALOG = `
    <dialog class="swl-dialog">
        <div class="swl-dialog-header"><h5><i></i><span></span></h5></div>
        <div id="swl-dialog-msg"></div>
        <button class="swl-btn-decline"></button>
        <button class="swl-btn-confirm"></button>
        <button class="swl-btn-ok"></button>
    </dialog>`;

QUnit.module("tree", (hooks) => {
    hooks.beforeEach(() => {
        recorded = [];
        window.tree_test_record = (kwargs) => recorded.push(kwargs);
        document.getElementById("qunit-fixture").innerHTML = '<div id="the_tree" style="display: none"></div>' + DIALOG;
    });
    hooks.afterEach(async () => {
        window.jQuery("#the_tree").jstree("destroy");
        document.querySelectorAll("dialog[open]").forEach((elem) => elem.close());
        await swl_action("/action/tree_test_set_nodes", {});
        delete window.tree_test_record;
    });

    QUnit.test("loads its nodes from the data action, with the params", async (assert) => {
        await init({params: {name: "q1"}, selected: "b", notify: false});
        assert.deepEqual(children("f1"), ["a", "b", "c"]);
        assert.deepEqual(tree().get_node("f1").data.posted, {name: "q1", node: "#", selected: "b"});
        assert.deepEqual(selected(), ["b"], "selected");
        assert.notEqual(document.getElementById("the_tree").style.display, "none", "shown");
        assert.equal(tree().get_node("f1", true).find("> a").text(), "Folder <b>1</b>", "text, not HTML");
        await pause();
        assert.deepEqual(recorded, [], "notify=false: the selection is not posted");
    });

    QUnit.test("html: true shows texts as HTML", async (assert) => {
        await init({html: true});
        assert.equal(tree().get_node("f1", true).find("> a").text(), "Folder 1");
    });

    QUnit.test("selected posts the select action by default", async (assert) => {
        await init({params: {name: "q1"}, selected: "c"});
        await waitFor(() => recorded.length == 1, "select");
        assert.deepEqual(recorded, [{action: "select", name: "q1", node: "c"}]);
    });

    QUnit.test("a click posts the select action", async (assert) => {
        await init({params: {name: "q1"}});
        tree().get_node("a", true).find("> a").trigger("click");
        await waitFor(() => recorded.length == 1, "select");
        assert.deepEqual(recorded, [{action: "select", name: "q1", node: "a"}]);
        assert.deepEqual(selected(), ["a"]);
    });

    QUnit.test("tree_select, with and without notify", async (assert) => {
        await init();
        window.tree_select({tree_id: "the_tree", node_id: "d", notify: false});
        assert.deepEqual(selected(), ["d"]);
        await pause();
        assert.deepEqual(recorded, []);
        window.tree_select({tree_id: "the_tree", node_id: "b"});
        await waitFor(() => recorded.length == 1, "select");
        assert.deepEqual(selected(), ["b"], "one at a time");
        assert.equal(recorded[0].node, "b");
    });

    QUnit.test("tree_rename, tree_create, tree_delete", async (assert) => {
        await init();
        window.tree_rename({tree_id: "the_tree", node_id: "a", text: "A <i>new</i>"});
        assert.equal(tree().get_node("a").text, "A <i>new</i>");
        assert.equal(tree().get_node("a", true).find("> a").text(), "A <i>new</i>");

        window.tree_create({tree_id: "the_tree", nodes: [
            {id: "e", text: "E", parent: "f2"},
            {id: "e1", text: "E1", parent: "e"},
            {id: "z", text: "Z", parent: "f1", position: 0},
        ], select: "e1", notify: false});
        assert.deepEqual(children("f2"), ["d", "e"]);
        assert.deepEqual(children("e"), ["e1"]);
        assert.deepEqual(children("f1"), ["z", "a", "b", "c"], "position");
        assert.deepEqual(selected(), ["e1"]);
        assert.ok(tree().is_open("e"), "opened to show the selection");

        window.tree_delete({tree_id: "the_tree", node_id: "e", select: "d", notify: false});
        assert.notOk(tree().get_node("e1"));
        assert.deepEqual(children("f2"), ["d"]);
        assert.deepEqual(selected(), ["d"]);
        await pause();
        assert.deepEqual(recorded, []);
    });

    QUnit.test("tree_refresh loads the nodes again, then selects", async (assert) => {
        await init();
        await swl_action("/action/tree_test_set_nodes", {id: ["x", "y"]});
        window.tree_refresh({tree_id: "#the_tree", select: "y", notify: false});
        await waitFor(() => tree().get_node("y"), "refresh");
        await pause(20);
        assert.deepEqual(children("#"), ["x", "y"]);
        assert.deepEqual(selected(), ["y"]);
    });

    QUnit.test("dnd 'same-parent': moves within a parent are posted", async (assert) => {
        await init({params: {name: "q1"}, dnd: "same-parent"});
        assert.ok(tree().move_node("a", "f1", 2), "a after b");  // positions as jstree counts them
        await waitFor(() => recorded.length == 1, "move");
        assert.deepEqual(recorded[0], {action: "move", name: "q1", node: "a", parent: "f1", position: "1", old_parent: "f1", old_position: "0"});
        assert.deepEqual(children("f1"), ["b", "a", "c"]);
        assert.notOk(tree().move_node("b", "f2", 0), "not to another parent");
        assert.deepEqual(children("f1"), ["b", "a", "c"]);
    });

    QUnit.test("dnd 'any' with types; folders cannot be dragged", async (assert) => {
        await init({dnd: "any", types: {"#": {valid_children: ["folder"]}, folder: {valid_children: ["item"]}, item: {valid_children: []}}});
        assert.ok(tree().move_node("a", "f2", "last"));
        await waitFor(() => recorded.length == 1, "move");
        assert.equal(recorded[0].parent, "f2");
        assert.deepEqual(children("f2"), ["d", "a"]);
        assert.notOk(tree().move_node("b", "d", 0), "an item holds no items");
        let dnd = tree().settings.dnd;
        assert.notOk(dnd.is_draggable([tree().get_node("f1")]), "a folder is not draggable");
        assert.ok(dnd.is_draggable([tree().get_node("b")]));
    });

    QUnit.test("a move the server refuses: the tree reloads", async (assert) => {
        await init({dnd: "same-parent"});
        let refreshed = new Promise((resolve) => window.jQuery("#the_tree").one("refresh.jstree", resolve));
        assert.ok(tree().move_node("c", "f1", 0));
        assert.deepEqual(children("f1"), ["c", "a", "b"], "moved in the browser");
        await refreshed;
        assert.deepEqual(children("f1"), ["a", "b", "c"], "back where the server has it");
        window.jQuery(".swl-dialog")[0]?.close();
    });

    QUnit.test("without dnd nothing moves", async (assert) => {
        await init();
        assert.notOk(tree().move_node("a", "f1", 3));
        assert.notOk(tree().settings.plugins.includes("dnd"));
    });

    QUnit.test("init again replaces the tree", async (assert) => {
        await init();
        await swl_action("/action/tree_test_set_nodes", {id: ["x"]});
        await init();
        assert.deepEqual(children("#"), ["x"]);
    });

    QUnit.test("a tree from the HTML in the element", async (assert) => {
        document.getElementById("the_tree").innerHTML = '<ul><li id="h1">One<ul><li id="h2">Two</li></ul></li></ul>';
        await init({data_url: null, html: true});
        assert.deepEqual(children("h1"), ["h2"]);
        tree().get_node("h1", true).find("> a").trigger("click");
        await waitFor(() => recorded.length == 1, "select");
        assert.equal(recorded[0].node, "h1");
    });
});

QUnit.module("swl_action result", () => {
    QUnit.test("true on success, false when the action fails", async (assert) => {
        document.getElementById("qunit-fixture").innerHTML = DIALOG;
        assert.true(await swl_action("/action/tree_test_set_nodes", {}));
        assert.false(await swl_action("/action/tree_test_fail", {}));
        document.querySelectorAll("dialog[open]").forEach((elem) => elem.close());
    });
});
