# SWL on htmx 4: migration guide

SWL now uses [htmx 4](https://four.htmx.org) in the browser instead of its own jQuery code.
The Python API (`swl.success()...`, `swl.fail()...`, actions, `register()`) stays the same; the
`data-swl-*` attributes in templates become `hx-*` attributes. This is a breaking change: every
application has to convert its templates and javascript when it upgrades.

## How it works now

1. An element with `hx-post="{{ register('my_action') }}"` posts to the action when it is
   clicked (buttons, links), changed (inputs, selects) or submitted (forms). Buttons and inputs
   post their enclosing form, like `data-swl-button` did.
2. The action returns `swl.success()...` as before. The response is now HTML plus headers:
   - every `hydrate(placeholder, data)` becomes an `<hx-partial>` that htmx swaps into the element
     with that id;
   - everything else (`call`, `rehydrate`, `open_modal`, `toast`, `reset_form`, ...) becomes an
     event in the `HX-Trigger` header, handled by `swl.js` after the content is in place, in the
     order you called the methods;
   - `redirect()` and `set_url()` become `HX-Redirect` and `HX-Replace-Url`;
   - a response without content is `204 No Content`; `swl.fail()` is `422` and shows its message.
3. Errors (403, 404, 500, network) are shown in the SWL dialog and never swapped into the page. A
   request that is redirected (for instance to the login page after the session expired) turns
   into a normal page load.

## Page setup

- `swl/base.j2` loads htmx (from the framework's resources, see "Styling" in `doc/reference.md`) and sets the htmx config
  `<meta name="htmx-config" content='{"noSwap": [204, 304, "4xx", "5xx"]}'>`. If your pages do
  not extend `base.j2`, add that meta tag and the htmx script yourself.
- If you configure your own resources file (`paths.resources`), add htmx to its scripts:

  ```json
  {
      "src": "https://cdn.jsdelivr.net/npm/htmx.org@4.0.0/dist/htmx.min.js",
      "integrity": "sha384-BvJpBiO8Kh31EqtJe5DRIeWrHWnCGkwytKs9NKFi86Hhw96dEqdEMzZDeK9iEGTc"
  }
  ```

- **jQuery is no longer loaded by default.** SWL does not need it. If your own code uses jQuery,
  add it to your resources.
- Load SWL as before: `<script type="module" id="swl-run" src="/static/swl/swl-run.js" lang="nl_NL"></script>`
  (and `websocket.js` if you use live updates).

## Templates

| Before | Now |
|---|---|
| `<button data-swl-button="URL">` | `<button hx-post="URL">` (posts the enclosing form, or the form named in `form="..."`) |
| `<a data-swl-button="URL">` | `<a hx-post="URL">` (posts only its own values) |
| `data-swl-change="URL"` on select, checkbox, radio, text input, textarea, date, number | `hx-post="URL"` (inputs post on `change`, which for text fields is on blur when the value changed) |
| `data-swl-change-timeout="500"` | `hx-trigger="input changed delay:500ms"` |
| `data-swl-enter="URL"` on a search field | `hx-post="URL" hx-trigger="keyup[key=='Enter']"` |
| `data-swl-change-on-hydrate` | add `load` to the trigger: `hx-trigger="load, change"` |
| `<div id="x" data-swl-placeholder="URL">` | `{{ placeholder("x", URL) }}`, see below |
| `data-swl-load-options="URL"` on a select | `hx-post="URL" hx-trigger="load"`, the action hydrates the select |
| `data-swl-argument-name="value"` | `hx-vals='{{ {"name": value}\|tojson }}'`; put `hx-vals:inherited` on a parent (e.g. a table row) to give all elements inside it the same values |
| `data-swl-confirm="Sure?"` | `hx-confirm="Sure?"` (still shows the SWL dialog) |
| `data-swl-validate="fn"` | unchanged |
| `data-swl-link="/page"` | `<a href="/page">` (and `target="..."` instead of `data-swl-link-target`) |
| `data-swl-link="/action/..."` | `<a hx-post="/action/...">` |
| `data-swl-context="URL"` | `hx-post="URL" hx-trigger="contextmenu prevent"`; `event_x`/`event_y` are still posted |
| `data-swl-tab="URL"` on a Bootstrap tab | `hx-post="URL" hx-trigger="show.bs.tab"`, plus `load, ` in the trigger of the tab that is active when the page loads (see "Tabs" in `doc/reference.md`) |
| `form="id"` / `data-swl-form="id"` on a non-form element | `hx-include="#id"` |
| `class="swl-disabled"` | the `disabled` attribute |

Remember that htmx 4 does not inherit attributes unless you ask for it: `hx-confirm` or `hx-vals`
on a parent only apply to its children when written as `hx-confirm:inherited` / `hx-vals:inherited`.

### Placeholders

`swl/placeholder.j2` has a macro for elements that load their own content:

```jinja
{% from "swl/placeholder.j2" import placeholder %}
{{ placeholder("placeholder-users_list", register('users_list'), context={"page": 1}, on_changed=[qid]) }}
```

It renders `<div id="placeholder-users_list" hx-post="..." hx-trigger="load, swl-refresh" hx-vals='{"page": 1}'>`.
The element posts its id as `placeholder` plus its `hx-vals`, and nothing else: not the fields
inside it or around it (use `hx-include` if it should post a form). With `lazy=True` it only loads
when rehydrated; `tag=` and `class_=` change the element.

## Rehydrate

Works as before, but the "recipe" lives on the element instead of in `sessionStorage`:

- `hydrate(placeholder, data, rehydrate=dict(action=..., context=...))` sets `hx-post` and
  `hx-vals` on the element, so it reloads from that action with that context.
- `rehydrate("placeholder-id", context={...})` reloads the element; `context` is added to that
  request only.
- From javascript: `swl.rehydrate("placeholder-id", {page: 2})`.
- Live updates: `on_changed=[...]` on the placeholder macro sets `data-swl-on-changed`; when the
  server signals a change of one of those qids, the placeholder reloads. Elements that are gone
  from the page are simply not reloaded any more.

## Modal, dialog, toast and context menu

SWL's modal, message dialog, toast and context menu are now native HTML (`<dialog>` and popovers)
styled by `swl.css`; they no longer need Bootstrap's javascript. Include `swl/modal.j2` and
`swl/contextmenu.j2` as before. Changes:

- Buttons in modal content that close it: `data-swl-close` (`data-bs-dismiss="modal"` still works).
- `swl/modal-content.j2` uses `swl-modal-*` classes instead of Bootstrap's `modal-header` /
  `modal-body`; it has a new optional `modal_footer` block.
- Put the items of a context menu in `<div class="swl-menu">` (buttons or links).
- Your own javascript that listened to `shown.bs.modal` / `hidden.bs.modal`: use the dialog's
  `close` event, or `swl-modal-shown` (fired on `#swl-modal` when it opens).
- A page with its own Bootstrap modal markup (`<div id="swl-modal" class="modal">`) still works,
  with Bootstrap's javascript.
- Bootstrap stays the default. With `"ui.framework": "bulma"` or `"swl"` (no framework) an
  application uses Bulma or SWL's own base styles instead (see "Styling" in `doc/reference.md`).

## Python

- Same methods on `swl.success()`, plus `trigger(event, **detail)` to fire your own javascript
  event (`document.addEventListener(event, e => ... e.detail ...)`).
- `hydrate()` data can no longer be an action URL that is fetched next. Put a placeholder in the
  returned HTML instead.
- `call(method, **kwargs)` still calls `window[method](kwargs)` after the content is swapped; a
  missing function is reported and does not stop the rest.
- Tests that checked `response.json()` must change: use `swl.test_utils.assert_success(response)`
  (returns the events) and `assert_fail(response, message)`.

## Kickstart

`kickstart` in `base.j2` still posts an action after the page has loaded, but now waits until the
page's placeholders have loaded too, so it can rebuild nested screens. Pass `kwargs` as a dict
(a JSON string still works); it is now escaped safely, so values from the url can go in as they
are. See "Deep links" in `doc/reference.md`.

## Javascript

- `swl.js` no longer exports `hydrate`, `start_hydrating`, `rehydrate_placeholder`,
  `arguments_from_elem` and `swl_arguments_from_elem`; `rehydrate.js` is gone.
- Available on `window`: `swl_action(url, values)` (also `swl.action`), `swl.kickstart(url, values)`, `swl.rehydrate(id, context)`,
  `swl.ui.confirm(message)` (a promise), `swl.ui.error(message)`, `swl.ui.info(message)`.
- HTML inserted by htmx is set up automatically. If your own code inserts HTML with `hx-*`
  attributes, call `htmx.process(element)` on it.
