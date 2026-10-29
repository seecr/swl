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
register("<function name>"), e.g. hx-post="{{ register('task_save') }}". SWL calls it with the
request and the keyword arguments registered with swl.register_action_kwargs(); here: swl, store
and dispatcher (and userbase, used by the account views).

Actions require a logged-in user unless registered with authenticated=False.

An action answers with swl.success() or swl.fail(), see swl/responses.py:
  .hydrate(id, html)        put html into the element with that id
  .rehydrate(id, context=)  let a placeholder reload itself
  .open_modal(html)         show html in the modal dialog
  .toast(text)              show a short message
  .call(function, **kw)     call a javascript function with kw
  .set_url(url, **params)   change the url in the address bar (see "Where you are: the url")
  swl.fail().message(text)  show an error message
"""

from types import SimpleNamespace
from urllib.parse import urlencode

from markupsafe import Markup, escape

from .store import TaskStore

TASKS_LIST = "tasks-list"  # id of the placeholder with the task list (page.j2)
TASK_DETAIL = "task-detail"  # id of the placeholder with the selected task (page.j2)
SELECTION = "selection"  # id of the hidden fields that remember the selected task and tab
STATUSES = ["all", "open", "done"]
TABS = ["details", "history"]


# --- Where you are: the url -------------------------------------------------------------------
#
# The screen is described by four things: the search text, the status filter, the selected task
# and its tab. They live in the #filters form (the last two as hidden fields, see selection.j2),
# so every request that includes #filters knows the whole screen, and actions put it in the url:
#
#     /tasks/<task id>/<tab>?q=<search>&status=<status>
#
# The page route (app.py) reads that url and renders the same screen, so a reload, a bookmark or
# a link to a colleague shows exactly what you saw.


def screen_from(form):
    """The screen as posted with the #filters form."""
    status = form.get("status", "all")
    tab = form.get("selected_tab")
    return {
        "q": form.get("q", "").strip(),
        "status": status if status in STATUSES else "all",
        "task_id": form.get("selected_task") or None,
        "tab": tab if tab in TABS else TABS[0],
    }


def page_url(q="", status="all", task_id=None, tab=TABS[0]):
    """The url of a screen: the selection in the path, the filters as query parameters."""
    path = f"/tasks/{task_id}/{tab}" if task_id else "/"
    params = {k: v for k, v in (("q", q), ("status", status)) if v and v != "all"}
    return path + ("?" + urlencode(params) if params else "")


def render_detail(swl, store, task_id, tab):
    """The detail panel (tabs + the content of the active tab), or a hint when nothing is selected.
    Used by the task_detail action and by the page route, which renders it straight into the page."""
    task = store.get(task_id) if task_id else None
    return swl.template("tasks/detail.j2").render(
        task=task, tab=tab, tabs=TABS, missing=task_id is not None and task is None
    )


def render_selection(task_id, tab):
    """The hidden fields in the #filters form that remember the selected task and tab."""
    return Markup(
        f'<input type="hidden" name="selected_task" value="{escape(task_id or "")}">'
        f'<input type="hidden" name="selected_tab" value="{escape(tab)}">'
    )


async def tasks_list(request, swl, store, **kwargs):
    """Renders the task list into its placeholder.

    Posted by the placeholder itself: when the page loads, when a filter changes (it includes the
    #filters form) and when it is rehydrated. A rehydrate can add "highlight" to mark a task."""
    async with request.form() as form:
        screen = screen_from(form)
        highlight = form.get("highlight")

    tasks = store.find(q=screen["q"], status=screen["status"])
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
        .call("show_counts", **store.counts())  # see static/tasks.js
    )


async def task_detail(request, swl, store, **kwargs):
    """Shows a task in the detail panel, on one of its tabs.

    Posted by a task title and by the tabs (with "task" and/or "tab" in hx-vals, plus the #filters
    form), and by the detail placeholder itself when it is rehydrated (only the #filters form: it
    then shows the task and tab that are selected already)."""
    async with request.form() as form:
        screen = screen_from(form)
        previous = screen["task_id"]
        screen["task_id"] = form.get("task") or previous
        if form.get("tab") in TABS:
            screen["tab"] = form["tab"]

    if screen["task_id"] and store.get(screen["task_id"]) is None:
        # deleted (maybe in another tab): show that once, then forget the selection
        html = render_detail(swl, store, screen["task_id"], screen["tab"])
        screen["task_id"] = None
    else:
        html = render_detail(swl, store, screen["task_id"], screen["tab"])

    response = (
        swl.success()
        .hydrate(TASK_DETAIL, html)
        .hydrate(SELECTION, render_selection(screen["task_id"], screen["tab"]))
        .set_url(page_url(**screen))
    )
    if screen["task_id"] != previous:
        response.rehydrate(TASKS_LIST)  # to move the "selected" mark in the list
    return response


async def task_new(request, swl, **kwargs):
    html = swl.template("tasks/form.j2").render(task=None)
    return swl.success().open_modal(html, call="focus_title")


async def task_edit(request, swl, store, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message("This task no longer exists")
    html = swl.template("tasks/form.j2").render(task=task)
    return swl.success().open_modal(html, call="focus_title")


async def task_save(request, swl, store, dispatcher, **kwargs):
    async with request.form() as form:
        task_id = form.get("task_id")
        title = form.get("title", "").strip()
        notes = form.get("notes", "").strip()

    if not title:
        return swl.fail().message("A task needs a title")

    if task_id:
        if store.get(task_id) is None:
            return swl.fail().message("This task no longer exists")
        task = store.update(task_id, title=title, notes=notes)
    else:
        task = store.add(title=title, notes=notes)

    await _signal_change(dispatcher, store)
    return (
        swl.success()
        .close_modal()
        .rehydrate(TASKS_LIST, TASK_DETAIL, context={"highlight": task.id})
        .toast("Task saved")
    )


async def task_toggle(request, swl, store, dispatcher, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message("This task no longer exists")
    store.toggle(task.id)
    await _signal_change(dispatcher, store)
    return swl.success().rehydrate(TASKS_LIST, TASK_DETAIL, context={"highlight": task.id})


async def task_delete(request, swl, store, dispatcher, **kwargs):
    task = await _task(request, store)
    if task is None:
        return swl.fail().message("This task no longer exists")
    store.delete(task.id)
    await _signal_change(dispatcher, store)
    return swl.success().rehydrate(TASKS_LIST, TASK_DETAIL).toast(f"Deleted '{task.title}'")


async def task_menu(request, swl, store, **kwargs):
    """Context menu (right click on a task). swl.js posts the click position as event_x/event_y."""
    async with request.form() as form:
        location = {"x": int(float(form["event_x"])), "y": int(float(form["event_y"]))}
    task = await _task(request, store)
    if task is None:
        return swl.success()
    html = swl.template("tasks/menu.j2").render(task=task)
    return swl.success().open_contextmenu(html, location=location)


async def _task(request, store):
    async with request.form() as form:
        return store.get(form.get("task_id", ""))


async def _signal_change(dispatcher, store):
    """Tell every open page (websocket.js) that the task list changed; placeholders with
    data-swl-on-changed="tasks" reload themselves. That includes other users and other tabs."""
    await dispatcher.signal_change(SimpleNamespace(qid=TaskStore.qid))


__actions__ = [
    tasks_list,
    task_detail,
    task_new,
    task_edit,
    task_save,
    task_toggle,
    task_delete,
    task_menu,
]
