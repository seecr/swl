---
title: "SWL"
news: "**SWL 5.0 is out.** The browser side is now [htmx 4](https://four.htmx.org), SWL is MIT licensed, and you can `pip install swl` from [PyPI](https://pypi.org/project/swl/). See the [changelog](https://github.com/seecr/swl/blob/main/CHANGELOG.md) for what to convert."
---

## introduction

SWL (Seecr Web Lib) lets you build interactive web applications in Python, without a JavaScript
frontend.

It is a small layer on top of [Starlette](https://www.starlette.io),
[Jinja](https://jinja.palletsprojects.com) and [htmx 4](https://four.htmx.org). The server
renders HTML. An action answers with a short list of instructions: *put this HTML there, reload
that list, close the dialog, show a toast*. SWL carries them out in the browser.

You write Python and templates. There is no build step, and no second application to keep in
sync.

SWL is made for the software around data: admin screens, editors, review tools, form builders
and dashboards. Lots of forms, lists, dialogs and tabs, used every day by people who need them
to work.

## motivation

- Why does a screen with a form and a list need two applications, an API and a JavaScript
  frontend, that have to be kept in sync?
- Why should the browser know how a list looks, when the server already renders it?
- Why do you need a build step and a `node_modules` folder for a dialog?
- Why test a button click in a browser, when the answer to it is just data?

Keep the server in charge of the HTML, let it say what should happen next, and let the browser
do it. That is SWL.

## quick start

```sh
pip install swl
```

A form that adds a note, and a list that loads itself:

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

SWL needs Python 3.11 or newer.

## what you get

<dl class="features">
<dt>actions</dt>
<dd>Async Python functions, registered by module, with login and authorisation checks. A
template gets an action's url with <code>register("name")</code>.</dd>

<dt>a response builder</dt>
<dd><code>hydrate</code>, <code>rehydrate</code>, <code>open_modal</code>,
<code>close_modal</code>, <code>open_contextmenu</code>, <code>toast</code>, <code>call</code>,
<code>set_url</code>, <code>redirect</code>, <code>trigger</code>, and
<code>swl.fail().message(...)</code> for errors.</dd>

<dt>placeholders</dt>
<dd>Parts of the page that load themselves and can be reloaded by name from any action.</dd>

<dt>live updates</dt>
<dd>A placeholder can reload when the data it shows changes, also in other browser tabs and for
other users, over a websocket.</dd>

<dt>deep links</dt>
<dd>Actions keep the url up to date, and a page route renders the same screen from it. Screens
survive a reload and can be shared.</dd>

<dt>ready-made parts</dt>
<dd>A modal, confirm and error dialogs, toasts and context menus, all plain HTML
(<code>&lt;dialog&gt;</code>, popover). Login, "my account" and user management screens.</dd>

<dt>your css framework</dt>
<dd>Bootstrap (the default), Tabler, Bulma, or SWL's own small stylesheet with no framework at
all. Light and dark work with each of them.</dd>
</dl>

## try the example

The example application is a small task list. It uses nearly everything: dialogs, search as you
type, tabs, a context menu, live updates between browser tabs, screens that survive a reload,
and switches for the CSS framework and dark mode.

```sh
git clone https://github.com/seecr/swl.git
cd swl
pip install -e . -e example/
python -m swl_tasks
```

Open <http://127.0.0.1:8000/> and log in as **demo** / **demo-password**.

## docs {#docs}

<div class="cards">
<a class="card" href="https://github.com/seecr/swl/blob/main/example/README.md">
<strong>the example, step by step</strong>
<span>A guided walk through the task list, from one click to the updated list. Start here.</span>
</a>
<a class="card" href="reference/">
<strong>reference</strong>
<span>Everything SWL provides, for looking things up. Also covers debugging and
troubleshooting.</span>
</a>
<a class="card card-pdf" href="swl-reference.pdf" download>
<strong>reference as pdf</strong>
<span>The same reference, as one document to print or read offline.</span>
</a>
<a class="card" href="https://github.com/seecr/swl/blob/main/CHANGELOG.md">
<strong>changelog</strong>
<span>What changed in each release, and what to convert when upgrading.</span>
</a>
</div>

## sources

SWL is open source under the MIT License.

- **Code:** [github.com/seecr/swl](https://github.com/seecr/swl)
- **Package:** [pypi.org/project/swl](https://pypi.org/project/swl/)
- **Issues:** [github.com/seecr/swl/issues](https://github.com/seecr/swl/issues)
- **Security problems:** see [SECURITY.md](https://github.com/seecr/swl/blob/main/SECURITY.md)

SWL is made and maintained by [Seecr](https://seecr.nl), who use it for their own
applications.

<figure class="quote">
<blockquote>Simplicity is prerequisite for reliability.</blockquote>
<figcaption>Edsger W. Dijkstra, <a href="https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD498.html">EWD 498</a> (1975)</figcaption>
</figure>
