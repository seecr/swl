# SWL Tasks: an example application

A small task list built with SWL (Seecr Web Lib). It is meant to be read: every SWL feature is
used at least once, in the simplest way that works, with comments that point to the rest.

What you can do in it:

- log in (and, as admin, manage users and change your password with SWL's built-in dialogs);
- add and edit tasks in a modal dialog, with a toast when they are saved;
- search and filter the list as you type;
- click a task to see it next to the list, on a **Details** or **History** tab;
- reload the page (or bookmark it, or send the link) and get back exactly where you were: the same
  task, on the same tab, with the same filter;
- tick tasks off, delete them after a confirmation, or right-click for a context menu;
- see changes appear in every other open tab straight away.

## Running it

From the root of the swl repository:

```sh
pip install -e .            # swl itself (needs seecr-stdlib)
pip install -e example/     # this example
python -m swl_tasks         # or: swl-tasks
```

Open <http://127.0.0.1:8000/> and log in as **demo** / **demo-password**. Tasks and users are
stored in `./swl-tasks-data` (change it with `--data-dir`; `--port` and `--host` work too).
`--framework bootstrap`, `--framework tabler` or `--framework bulma` shows the same app in that CSS framework; the
switches in the top bar change the framework and light/dark colours while you use it.

Run the tests with `pytest example/swl_tasks`.

## The files

```
example/
├── pyproject.toml
├── README.md                this file
└── swl_tasks/
    ├── app.py               wires SWL, the pages, sessions and the websocket together
    ├── views.py             the actions: everything the page can ask the server to do
    ├── store.py             where tasks are kept (plain Python, nothing SWL-specific)
    ├── __main__.py          python -m swl_tasks
    ├── app_test.py          tests for the actions
    ├── templates/tasks/
    │   ├── page.j2          the page: navigation, filters, the task list and the detail panel
    │   ├── list.j2          the task list (rendered by the tasks_list action)
    │   ├── detail.j2        the detail panel with its tabs (rendered by task_detail)
    │   ├── tab_details.j2   the content of the "Details" tab
    │   ├── tab_history.j2   the content of the "History" tab
    │   ├── form.j2          the new/edit form (shown in the modal)
    │   ├── menu.j2          the context menu
    │   ├── style_switch.j2  the CSS framework and light/dark switches in the top bar
    │   └── login.j2         the login page
    └── static/
        ├── tasks.js         two small functions the server calls, and the look switches
        └── tasks.css        a few styles
```

## How SWL works, using this example

### 1. The page is ordinary HTML

`page.j2` extends `swl/base.j2`, which brings in htmx, SWL's styles, the message dialog and the
toast. By default there is no CSS framework: `app.py` sets `"ui.framework": "swl"`, which loads
SWL's own `swl-base.css`. Run it with `--framework bootstrap`, `tabler` or `bulma` to see the
same app in those frameworks: the templates take the classes of form elements and buttons from
`SWL.ui` (e.g. `class="{{ SWL.ui.button_primary }}"`) and use SWL's `swl-*` layout classes (see
"Styling" in `doc/reference.md`). The page includes the modal (`swl/modal.j2`) and the context menu
(`swl/contextmenu.j2`) because it uses them, and loads SWL's javascript at the end:

```html
<script type="module" id="swl-run" src="/static/swl/swl-run.js" lang="en_US"></script>
<script type="module" src="/static/swl/websocket.js"></script>
```

The page itself is served by a normal route in `app.py`. `swl.endpoint(page, redirect="/login")`
wraps it so only logged-in users see it; anyone else is sent to the login page.

### 2. Actions are Python functions

Everything interactive is an **action**: an async function in `views.py`, listed in
`__actions__` and registered in `app.py`:

```python
swl.register_modules(account, views)
swl.register_action_kwargs(userbase=userbase, store=store, dispatcher=dispatcher)
```

Each action gets the request plus those keyword arguments (and `swl` itself). Actions need a
logged-in user unless they are registered with `authenticated=False`, like `login` in
`swl.views.account`.

A template gets the url of an action with `register()`:

```html
<button type="button" class="primary" hx-post="{{ register('task_new') }}">New task</button>
```

`register('task_new')` gives `/action/<hash of the name>`, and fails while rendering if no such
action exists, so a typo shows up at once.

### 3. htmx sends the request

The `hx-post` attribute is [htmx](https://four.htmx.org): clicking the button posts to the
action. What gets posted:

- a button or form field posts its form (the task form posts `title`, `notes` and `task_id`);
- `hx-vals` adds values. Every row in `list.j2` has
  `hx-vals:inherited='{"task_id": "..."}'`, so the checkbox, the delete button and the
  context menu in that row all post the task id;
- a placeholder or link posts only its own values plus the fields in its `hx-include`.

Other htmx attributes in the example: `hx-confirm` (shown in SWL's own dialog),
`hx-trigger="contextmenu prevent"` (right click, without the browser's menu) and the triggers of
the task list placeholder (below).

### 4. The action answers with instructions

An action returns `swl.success()` with what should happen in the browser, in the order it should
happen. Saving a task:

```python
return (
    swl.success()
    .close_modal()
    .rehydrate(TASKS_LIST, context={"highlight": task.id})
    .toast("Task saved")
)
```

or, when something is wrong:

```python
return swl.fail().message("A task needs a title")
```

The methods used in the example:

| Method | What happens in the browser | Used in |
|---|---|---|
| `hydrate(id, html)` | the element with that id gets `html` as its content | `tasks_list`, `task_detail` |
| `rehydrate(id, ..., context=...)` | those placeholders reload themselves, with `context` added | `task_save`, `task_toggle`, `task_delete`, `task_detail` |
| `open_modal(html, call=...)` | `html` is shown in the modal; `call` runs when it is visible | `task_new`, `task_edit` |
| `close_modal()` | the modal closes | `task_save` |
| `open_contextmenu(html, location)` | `html` is shown as a menu at the click position | `task_menu` |
| `toast(text)` | a short message in the corner | `task_save`, `task_delete` |
| `call(function, **kwargs)` | `window[function](kwargs)` runs | `tasks_list` (`show_counts` in `tasks.js`) |
| `set_url(url, **params)` | the address bar changes, without a page load | `tasks_list`, `task_detail` |
| `redirect(url)` | the browser goes to `url` | `login` (in `swl.views.account`) |
| `fail().message(text)` | the message is shown in the error dialog | several |

Templates are rendered with `swl.template("tasks/list.j2").render(...)`; `register()` is available
in them too.

### 5. Placeholders load and reload themselves

The task list is not part of the page. `page.j2` only has a **placeholder** for it:

```jinja
{{ placeholder("tasks-list", register('tasks_list'),
               trigger="input delay:300ms from:#filters",
               attrs={"hx-include": "#filters", "hx-sync": "this:queue last"},
               on_changed=["tasks"]) }}
```

That renders `<div id="tasks-list" hx-post="..." hx-trigger="load, swl-refresh, ...">`, which
posts to the `tasks_list` action:

- when the page loads (`load`);
- when it is **rehydrated** (`swl-refresh`): by an action (`.rehydrate("tasks-list")`) or by
  javascript (`swl.rehydrate("tasks-list")`);
- 300 ms after you type in the search field or change the select (`input ... from:#filters`).
  `hx-include` makes it post the filter form, and `hx-sync` keeps fast typing from mixing up
  the order of the answers;
- when the server says that `tasks` changed (`on_changed`, see 6).

`tasks_list` reads the filters, renders `list.j2` and hydrates the placeholder with it.

The other actions **don't render the list**. `task_save` only says "rehydrate the task list,
and highlight this task"; the placeholder knows how to reload itself and posts the current
filters with it. That is the point of rehydrate: an action can refresh any part of the page
without knowing how that part is rendered. Adding a "recent tasks" panel later would not change
`task_save` at all, apart from naming one more placeholder.

### 6. Live updates in other tabs

After a change, the actions call:

```python
await dispatcher.signal_change(SimpleNamespace(qid="tasks"))
```

The `Dispatcher` (a websocket at `/ws`, set up in `app.py`) tells every open page that `tasks`
changed. `websocket.js` reloads every placeholder with `data-swl-on-changed` containing `tasks`,
which `on_changed=["tasks"]` added to the task list. So a task ticked off in one tab is ticked off
in every other tab and for every other user, with no extra code. In a real application the qid
would name the object that changed, e.g. a project, so only the pages showing that project
reload.

### 7. Tabs, and where you are: `set_url`

Click a task title and it appears on the right, on its **Details** tab; click **History** to see
what happened to it. Reload the page: same task, same tab, same filter. Three things make that
work.

**The screen is kept in the `#filters` form.** Next to the search field and the status select,
the form has two hidden fields, `selected_task` and `selected_tab` (in `<span id="selection">`).
The list, the detail panel, the titles and the tabs all include `#filters` in their requests, so
every action knows the whole screen.

**Actions put the screen in the url.** `views.page_url()` turns it into an address:

```
/tasks/<task id>/<tab>?q=<search>&status=<status>
```

and `tasks_list` and `task_detail` end with `.set_url(page_url(**screen))`. The address bar
follows every click and filter, without loading a page.

**The page route renders that url.** `app.py` sends `/`, `/tasks/{task_id}` and
`/tasks/{task_id}/{tab}` to the same `page` function. It reads the filters from the query and the
selection from the path, fills in the hidden fields and renders the detail panel straight into the
page with `views.render_detail()`, the same function the action uses. So after a reload the panel
is simply there; only the task list loads itself (one request), and it marks the selected task
because the selection is in `#filters`. No extra round trips, nothing to replay.

**The tabs are buttons.** Each one calls `task_detail` with the task and its tab:

```html
<button type="button" role="tab" aria-selected="true"
        hx-post="{{ register('task_detail') }}" hx-include="#filters"
        hx-vals='{"task": "3f2a...", "tab": "history"}'>History</button>
```

The action renders the whole panel again with that tab active (only the active tab's content is
rendered), hydrates `#task-detail`, hydrates `#selection` with the new hidden fields, and sets the
url:

```python
return (
    swl.success()
    .hydrate(TASK_DETAIL, html)
    .hydrate(SELECTION, render_selection(screen["task_id"], screen["tab"]))
    .set_url(page_url(**screen))
)
```

When a *different* task was selected, it also rehydrates the list to move the selection mark. A
title click is the same action without a tab (so the first tab), and the panel's own rehydrate
(after a change) is the same action without a task (so whatever is selected).

Some details:

- The values in the url are user input: `screen_from()` only accepts known statuses and tabs, and
  a link to a task that no longer exists shows "This task no longer exists" instead of an error.
- `set_url` replaces the address, so the Back button leaves the page rather than going back one
  tab. To change that, the actions would push the url instead.
- Tabs that switch panes in the browser (Bootstrap's, each loading its content when shown) work
  too in an application that uses Bootstrap; `doc/reference.md` shows both ways.

### 8. A walk through one click

Ticking off a task:

1. The checkbox has `hx-post="{{ register('task_toggle') }}"` and its row has
   `hx-vals:inherited='{"task_id": "3f2a..."}'`. htmx posts `task_id=3f2a...` to the action.
2. `task_toggle` flips the task in the store, signals the change and returns
   `swl.success().rehydrate("tasks-list", "task-detail", context={"highlight": "3f2a..."})`.
3. That response has no content (204) and the header
   `HX-Trigger: {"swl-rehydrate": {"placeholders": {"tasks-list": {"highlight": "3f2a..."}, "task-detail": {...}}}}`.
4. `swl.js` handles `swl-rehydrate`: both placeholders post to their action with `#filters` and
   `highlight=3f2a...`.
5. `tasks_list` answers with the new list (`<hx-partial hx-target="#tasks-list">...`), the address
   bar url and a call to `show_counts`. htmx swaps the list in; the ticked task is highlighted;
   `show_counts` updates the badge and the window title. `task_detail` answers with the selected
   task, so the panel shows its new status (and the History tab its new entry).
6. Meanwhile every other open tab got the websocket message and reloaded its own list and panel.

### 9. Testing

Actions are tested like any Starlette endpoint, by posting to their url. `swl.test_utils` has
helpers for SWL responses:

```python
response = client.post(action(client, "task_save"), data={"title": "Write example"})
assert assert_success(response) == {
    "swl-modal-close": {},
    "swl-rehydrate": {"placeholders": {"tasks-list": {"highlight": task.id}}},
    "swl-toast": {"delay": 500},
}

assert_fail(client.post(action(client, "task_save"), data={"title": ""}), "A task needs a title")
```

`assert_success` returns the events of the response, so the test reads like the action. See
`app_test.py` for the rest, including the tabs, a reload of a deep link (`client.get("/tasks/...")`)
and the websocket.

## Where to go from here

- `doc/reference.md` in the swl repository lists everything SWL provides, what each kind of
  element posts, how to debug, and answers to common problems.
- `doc/htmx-migration.md` in the swl repository lists every `data-swl-*` attribute of older SWL
  versions and its htmx equivalent.
- `swl/responses.py` documents all response methods; `swl/templates/swl/placeholder.j2` the
  placeholder options.
- The [htmx 4 documentation](https://four.htmx.org) covers the `hx-*` attributes.
