# SWL (Seecr Web Lib)

[![Tests](https://github.com/seecr/swl/actions/workflows/test.yml/badge.svg)](https://github.com/seecr/swl/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/swl.svg)](https://pypi.org/project/swl/)

Interactive web applications in Python, without a JavaScript frontend.

SWL is a small layer on top of [Starlette](https://www.starlette.io),
[Jinja](https://jinja.palletsprojects.com) and [htmx 4](https://four.htmx.org). The server renders
HTML; an action answers with a short list of instructions ("put this HTML there, reload that list,
close the dialog, show a toast") that SWL carries out in the browser. You write Python and
templates. There is no build step, and no second application to keep in sync.

It is made for the software around data: admin screens, editors, review tools, form builders and
dashboards. These are lots of forms, lists, dialogs and tabs, used every day by people who need
them to work.

## A taste

```jinja
{% from "swl/placeholder.j2" import placeholder %}

<form hx-post="{{ register('note_add') }}">
    <input name="text" class="{{ SWL.ui.input }}">
    <button type="submit" class="{{ SWL.ui.button_primary }}">Add</button>
</form>

{{ placeholder("notes", register('notes_list')) }}
```

```python
async def notes_list(request, swl, db, **kwargs):
    html = swl.template("notes/list.j2").render(notes=db.notes())
    return swl.success().hydrate("notes", html)


async def note_add(request, swl, db, **kwargs):
    async with request.form() as form:
        text = form.get("text", "").strip()
    if not text:
        return swl.fail().message("A note needs some text")
    db.add_note(text)
    return swl.success().reset_form().rehydrate("notes").toast("Note added")


__actions__ = [notes_list, note_add]
```

`note_add` doesn't render the list. It asks the list to reload itself, so `notes_list` stays the
only place that knows how the list looks. And because a response is data, you test an action
without a browser.

## What you get

- **Actions**: async Python functions, registered by module, with login and authorisation checks.
  A template gets an action's url with `register("name")`.
- **A response builder**: `hydrate`, `rehydrate`, `open_modal`, `close_modal`,
  `open_contextmenu`, `toast`, `call` (a JavaScript function), `set_url`, `redirect`,
  `trigger`, and `swl.fail().message(...)` for errors.
- **Placeholders and rehydrate**: parts of the page that load themselves and can be reloaded by
  name from any action.
- **Live updates**: a placeholder can reload when the data it shows changes, also in other
  browser tabs and for other users (over a websocket).
- **Screens you can reload and link to**: actions keep the url up to date, and a page route
  renders the same screen from it.
- **Ready-made parts**: a modal, confirm and error dialogs, toasts and context menus, all
  plain HTML (`<dialog>`, popover). There are also login, "my account" and user management
  screens.
- **Your choice of CSS framework**: `ui.framework` is `"bootstrap"` (the default), `"tabler"`,
  `"bulma"` or `"swl"`, SWL's own small stylesheet with no framework at all. Light and dark
  colours work with each of them.

## Install

```sh
pip install swl
```

Or from a checkout: `pip install -e .`. SWL needs Python 3.11 or newer. Its dependencies, including `seecr-stdlib`, come from PyPI.

## Try the example

The example application is a small task list. It uses nearly everything: dialogs, search as you
type, tabs, a context menu, live updates between browser tabs, screens that survive a reload,
and switches for the CSS framework and dark mode.

```sh
pip install -e .
pip install -e example/
python -m swl_tasks
```

Open <http://127.0.0.1:8000/> and log in as **demo** / **demo-password**.

## Documentation

- [`example/README.md`](example/README.md): a guided walk through the example, from one click to
  the updated list. Start here.
- [`doc/reference.md`](doc/reference.md): everything SWL provides, for looking things up. Also
  covers debugging and troubleshooting.
- [`CHANGELOG.md`](CHANGELOG.md): what changed.

## Tests

```sh
pytest swl example/swl_tasks
```

The JavaScript tests (QUnit) run in a browser: `python -m swl.test.server`, then open
<http://localhost:8000/>.

## License

SWL is released under the MIT License; see [LICENSE](LICENSE).

Copyright © Seecr (Seek You Too B.V.), <https://seecr.nl>.
