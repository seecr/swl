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
The actions of the example.

Every function listed in __actions__ is an SWL action. Templates get its url with
register("<function name>"), e.g. hx-post="{{ register('task_save') }}". SWL calls it with
the request and the keyword arguments registered with swl.register_action_kwargs(); here:
swl, store and dispatcher (and userbase, used by the account views).

Actions require a logged-in user unless registered with authenticated=False.

An action answers with swl.success() or swl.fail(), see swl/responses.py:
  .hydrate(id, html)        put html into the element with that id
  .rehydrate(id, context=)  let a placeholder reload itself
  .open_modal(html)         show html in the modal dialog
  .toast(text)              show a short message
  .call(function, **kw)     call a javascript function with kw (e.g. tree_init, see
                            "The tree" below)
  .set_url(url, **params)   change the url in the address bar
                            (see "Where you are: the url")
  swl.fail().message(text)  show an error message

Texts are written in English and marked with _() (or N_ for constants), so they show in
the visitor's language (see "Translations" in the README).
"""

from types import SimpleNamespace
from urllib.parse import urlencode

from markupsafe import Markup, escape
from starlette.responses import JSONResponse

from swl.i18n import N_, _
from swl.tree import tree_node

from .store import TaskStore

TASKS_LIST = "tasks-list"  # id of the placeholder with the task list (page.j2)
TASK_DETAIL = "task-detail"  # id of the placeholder with the selected task (page.j2)
SELECTION = "selection"  # id of the hidden fields that remember the selected task and tab
TASK_TREE = "task-tree"  # id of the tree (tree.j2), in the "tasks-list" placeholder
STATUSES = ["all", "open", "done"]
TABS = ["details", "history"]
VIEWS = ["list", "tree"]  # the tasks as a table (list.j2) or as a tree (tree.j2)
# what the select and the tabs show; translated where they are shown
LABELS = {
    "all": N_("All"),
    "open": N_("Open"),
    "done": N_("Done"),
    "details": N_("Details"),
    "history": N_("History"),
    "list": N_("List"),
    "tree": N_("Tree"),
}


# --- Where you are: the url -------------------------------------------------------------
#
# The screen is described by five things: the search text, the status filter, the view
# (list or tree), the selected task and its tab. They live in the #filters form (the last
# two as hidden fields, see selection.j2), so every request that includes #filters knows
# the whole screen, and actions put it in the url:
#
#     /tasks/<task id>/<tab>?q=<search>&status=<status>&view=tree
#
# The page route (app.py) reads that url and renders the same screen, so a reload, a
# bookmark or a link to a colleague shows exactly what you saw.


def screen_from(form):
    """The screen as posted with the #filters form."""
    status = form.get("status", "all")
    tab = form.get("selected_tab")
    view = form.get("view")
    return {
        "q": form.get("q", "").strip(),
        "status": status if status in STATUSES else "all",
        "view": view if view in VIEWS else VIEWS[0],
        "task_id": form.get("selected_task") or None,
        "tab": tab if tab in TABS else TABS[0],
    }


def page_url(q="", status="all", view=VIEWS[0], task_id=None, tab=TABS[0]):
    """The url of a screen: the selection in the path, the filters as query parameters."""
    path = f"/tasks/{task_id}/{tab}" if task_id else "/"
    params = {
        k: v
        for k, v in (("q", q), ("status", status), ("view", view))
        if v and v not in ("all", VIEWS[0])
    }
    return path + ("?" + urlencode(params) if params else "")


def render_detail(swl, store, username, task_id, tab):
    """The detail panel (tabs + the content of the active tab), or a hint when nothing is
    selected. Used by the task_detail action and by the page route, which renders it
    straight into the page."""
    task = store.get(task_id, username) if task_id else None
    return swl.template("tasks/detail.j2").render(
        task=task,
        tab=tab,
        tabs=TABS,
        labels=LABELS,
        missing=task_id is not None and task is None,
    )


def render_selection(task_id, tab):
    """The hidden fields in the #filters form that remember the selected task and tab."""
    return Markup(
        f'<input type="hidden" name="selected_task" value="{escape(task_id or "")}">'
        f'<input type="hidden" name="selected_tab" value="{escape(tab)}">'
    )


async def tasks_list(request, swl, store, **kwargs):
    """Renders the task list into its placeholder.

    Posted by the placeholder itself: when the page loads, when a filter changes (it
    includes the #filters form) and when it is rehydrated. A rehydrate can add "highlight"
    to mark a task."""
    async with request.form() as form:
        screen = screen_from(form)
        highlight = form.get("highlight")

    username = request.user.username
    if screen["view"] == "tree":
        return tree_view(swl, store, username, screen)
    tasks = store.find(username, q=screen["q"], status=screen["status"])
    html = swl.template("tasks/list.j2").render(
        tasks=tasks,
        highlight=highlight,
        selected=screen["task_id"],
        filtered=bool(screen["q"]) or screen["status"] != "all",
    )
    return (
        swl.success()
        .hydrate(TASKS_LIST, html)
        .set_url(page_url(**screen))  # the filters changed: put them in the address bar
        .call("show_counts", **counts_text(store.counts(username)))  # static/tasks.js
    )


def counts_text(counts):
    return {
        "open": counts["open"],
        "text": _("%(open)d open / %(done)d done", **counts),
    }


async def task_detail(request, swl, store, **kwargs):
    """Shows a task in the detail panel, on one of its tabs.

    Posted by a task title and by the tabs (with "task" and/or "tab" in hx-vals, plus the
    #filters form), and by the detail placeholder itself when it is rehydrated (only the
    #filters form: it then shows the task and tab that are selected already)."""
    async with request.form() as form:
        screen = screen_from(form)
        previous = screen["task_id"]
        screen["task_id"] = form.get("task") or previous
        if form.get("tab") in TABS:
            screen["tab"] = form["tab"]

    response = show_task(swl, store, request.user.username, screen)
    if screen["task_id"] != previous and screen["view"] == "list":
        response.rehydrate(TASKS_LIST)  # to move the "selected" mark in the list
    return response


def show_task(swl, store, username, screen):
    """The response that shows the task of the screen in the detail panel, remembers it as
    the selection and puts it in the url."""
    html = render_detail(swl, store, username, screen["task_id"], screen["tab"])
    if screen["task_id"] and store.get(screen["task_id"], username) is None:
        # deleted (maybe in another tab): show that once, then forget the selection
        screen["task_id"] = None
    return (
        swl.success()
        .hydrate(TASK_DETAIL, html)
        .hydrate(SELECTION, render_selection(screen["task_id"], screen["tab"]))
        .set_url(page_url(**screen))
    )


async def task_new(request, swl, **kwargs):
    html = swl.template("tasks/form.j2").render(
        task=None, username=request.user.username
    )
    return swl.success().open_modal(html, call="focus_title")


async def task_edit(request, swl, store, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message(_("This task no longer exists"))
    html = swl.template("tasks/form.j2").render(
        task=task, username=request.user.username
    )
    return swl.success().open_modal(html, call="focus_title")


async def task_save(request, swl, store, dispatcher, **kwargs):
    async with request.form() as form:
        task_id = form.get("task_id")
        title = form.get("title", "").strip()
        notes = form.get("notes", "").strip()
        private = form.get("private") is not None

    if not title:
        return swl.fail().message(_("A task needs a title"))

    username = request.user.username
    if task_id:
        if (task := store.get(task_id, username)) is None:
            return swl.fail().message(_("This task no longer exists"))
        if task.owner != username and private:
            return swl.fail().message(_("Only its owner can make a task private"))
        was_private = task.private
        task = store.update(task_id, title=title, notes=notes, private=private)
    else:
        task = store.add(title=title, owner=username, notes=notes, private=private)
        was_private = private

    await _signal_change(dispatcher, task, was_private)
    return (
        swl.success()
        .close_modal()
        .rehydrate(TASKS_LIST, TASK_DETAIL, context={"highlight": task.id})
        .toast(_("Task saved"))
    )


async def task_toggle(request, swl, store, dispatcher, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message(_("This task no longer exists"))
    store.toggle(task.id)
    await _signal_change(dispatcher, task)
    return swl.success().rehydrate(
        TASKS_LIST, TASK_DETAIL, context={"highlight": task.id}
    )


async def task_delete(request, swl, store, dispatcher, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message(_("This task no longer exists"))
    store.delete(task.id)
    await _signal_change(dispatcher, task)
    return (
        swl.success()
        .rehydrate(TASKS_LIST, TASK_DETAIL)
        .toast(_("Deleted '%(title)s'", title=task.title))
    )


async def task_menu(request, swl, store, **kwargs):
    """Context menu (right click on a task). swl.js posts the click position as
    event_x/event_y."""
    async with request.form() as form:
        location = {
            "x": int(float(form["event_x"])),
            "y": int(float(form["event_y"])),
        }
    task = await _task(request, store)
    if task is None:
        return swl.success()
    html = swl.template("tasks/menu.j2").render(task=task)
    return swl.success().open_contextmenu(html, location=location)


# --- The tree ---------------------------------------------------------------------------
#
# With "Tree" chosen in the #filters form, the tasks_list action renders tree.j2 (an empty
# element) and calls tree_init (swl/static/swl/tree.js, which uses jstree). The tree then
# talks to the server by itself:
#   - it loads its nodes from task_tree_data (JSON, made with swl.tree.tree_node),
#   - a click on a task posts task_tree_select, which shows the task on the right,
#   - dragging a task posts task_tree_move: to reorder it, or to move it between Open and
#     Done. When that fails (the task was deleted meanwhile), the tree reloads itself.
# Every request also posts the params given to tree_init: here the filters.
# It sits in the "tasks-list" placeholder, so a change (here or in another tab) builds it
# again, as it does the list.

TREE_TYPES = {  # what may go where (jstree's types plugin): tasks only into a status
    "#": {"valid_children": ["status"]},
    "status": {"valid_children": ["task"]},
    "task": {"valid_children": []},
}
STATUS_ICONS = {"open": "bi bi-circle", "done": "bi bi-check-circle"}


def tree_view(swl, store, username, screen):
    """The tasks_list action with view=tree: the tree element, and tree_init to fill
    it."""
    html = swl.template("tasks/tree.j2").render(tree_id=TASK_TREE)
    return (
        swl.success()
        .hydrate(TASKS_LIST, html)
        .set_url(page_url(**screen))
        .call("show_counts", **counts_text(store.counts(username)))
        .call(
            "tree_init",
            tree_id=TASK_TREE,
            data_url=swl.register("task_tree_data"),
            select_url=swl.register("task_tree_select"),
            move_url=swl.register("task_tree_move"),
            params={"q": screen["q"], "status": screen["status"]},
            # the page already shows the selected task: only mark it in the tree
            selected=screen["task_id"],
            notify=False,
            dnd="any",
            types=TREE_TYPES,
        )
    )


async def task_tree_data(request, swl, store, **kwargs):
    """The nodes of the tree: the statuses, with the tasks in them. All at once, as a flat
    list in which every node names its parent ("#" is the top)."""
    async with request.form() as form:
        q = form.get("q", "")
        status = form.get("status", "all")

    username = request.user.username
    nodes = []
    for name in ("open", "done"):
        if status not in ("all", name):
            continue
        tasks = store.find(username, q=q, status=name)
        nodes.append(
            tree_node(
                f"status-{name}",
                f"{_(LABELS[name])} ({len(tasks)})",
                parent="#",
                type="status",
                icon=STATUS_ICONS[name],
                opened=True,
                draggable=False,
            )
        )
        nodes.extend(
            tree_node(
                task.id,
                task.title,  # text: tree.js shows it as text, not HTML
                parent=f"status-{name}",
                type="task",
                icon="bi bi-lock" if task.private else "bi bi-card-text",
            )
            for task in tasks
        )
    return JSONResponse(nodes)


async def task_tree_select(request, swl, store, **kwargs):
    """A click on a node in the tree: tree.js posts its id as "node", with the params.
    A task shows in the detail panel, on its first tab; a status does nothing."""
    async with request.form() as form:
        node = form.get("node", "")
        screen = screen_from({**form, "view": "tree", "selected_task": node})

    if node.startswith("status-"):
        return swl.success()
    return show_task(swl, store, request.user.username, screen)


async def task_tree_move(request, swl, store, dispatcher, **kwargs):
    """A task dragged in the tree. tree.js posts node, parent and position (among its
    new siblings, from 0), old_parent and old_position, and the params. A failure makes
    the tree reload, so the task goes back to where it is."""
    async with request.form() as form:
        task_id = form.get("node", "")
        parent = form.get("parent", "")
        q = form.get("q", "")
        try:
            position = int(form.get("position", ""))
        except ValueError:
            return swl.fail().message(_("Invalid position"))

    if (task := store.get(task_id, request.user.username)) is None:
        return swl.fail().message(_("This task no longer exists"))
    if parent not in ("status-open", "status-done"):
        return swl.fail().message(_("A task can only go into Open or Done"))

    store.move(
        task.id,
        request.user.username,
        done=parent == "status-done",
        position=position,
        q=q,
    )
    await _signal_change(dispatcher, task)  # other tabs; this one rebuilds its tree too
    return swl.success()


async def _task(request, store):
    """The task posted as task_id, if this user may see it."""
    async with request.form() as form:
        return store.get(form.get("task_id", ""), request.user.username)


async def _signal_change(dispatcher, task, was_private=None):
    """Tell the open pages (websocket.js) that the task list changed; placeholders with
    data-swl-on-changed="tasks" reload themselves. That includes other tabs.

    A shared task concerns everyone. A private task (before and after the change) concerns
    only its owner: then only the owner's pages hear about it. Other users do not even
    learn that something changed (Dispatcher.signal_change(..., users=[...]))."""
    private = task.private and (was_private is None or was_private)
    users = [task.owner] if private else None  # None: everyone
    await dispatcher.signal_change(SimpleNamespace(qid=TaskStore.qid), users=users)


__actions__ = [
    tasks_list,
    task_detail,
    task_new,
    task_edit,
    task_save,
    task_toggle,
    task_delete,
    task_menu,
    task_tree_data,
    task_tree_select,
    task_tree_move,
]
