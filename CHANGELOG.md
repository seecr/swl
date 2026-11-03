# Changelog

## Unreleased

### Changed

- The form field macros of `swl/inputs.j2` (`text_input`, `password_input`, `number_input`,
  `date_input`, `textarea_input`) put the label above the control (`swl-field`) with the
  framework's classes (`SWL.ui`), like SWL's own forms, instead of Bootstrap floating labels.
  They now look right with every `ui.framework`. The arguments stay the same; the controls no
  longer get a `placeholder` (the floating label needed it). `floating_label` is still there
  for templates that import it.
- `mandatory=True` of those macros now makes the control `required`; it did nothing before.

### Added

- `optional=True` for the `swl/inputs.j2` macros: "(optional)" after the label, quiet and
  never split over two lines (`swl-optional`). When most fields are required, mark the few
  optional ones instead of every required one. Translated in Dutch, German, French and
  Spanish.
- `hint="..."`: a help text below the control (`swl-hint`, linked with `aria-describedby`),
  and `id="..."`: a fixed id instead of a random one.
- `swl.success().saved(id)`: "✓ Saved" for a moment at an element, for fields that save
  themselves when they change; in its `.swl-saved` element, or one added at its end
  (`role="status"`). Fades out after `delay` ms (config `response.saved.delay`, 2500). The
  text is translated (`saved` in SWL's texts).

## 5.3.0 (2026-11-01)

### Added

- `Dispatcher.signal_change(obj, users=[...])` sends a change only to the open pages of those
  users (their `websocket.user.identity`), so a qid that tells something, like a private
  conversation, does not reach everyone. `obj` may also be the qid itself.
- `Dispatcher(authenticated=True)` refuses websockets without a logged-in user (close code
  1008); `Dispatcher(identify=fn)` links a websocket to an identity in another way.
- `Dispatcher.connected_users()`: the identities with at least one open page.
- `Dispatcher.user_connected(identity)` and `user_disconnected(identity)`: hooks for
  subclasses, called when a user's first page connects and their last page closes (e.g.
  to show who is online).
- `Dispatcher(idle_timeout=...)` closes a page that sent nothing (no ping) for that many
  seconds, so a sleeping phone or a lost network does not stay "online".
- `UserbaseUser.identity`: the username.
- `websocket.js` reloads every placeholder with `data-swl-on-changed` after a reconnect, so
  changes signalled while the connection was down are not missed. It notices a dead connection
  by a ping without an answer (5 s), and pings at once when the page becomes visible again or
  the browser comes back online.
- Translations (`swl.i18n`): texts marked with `_()` / `ngettext` / `N_` in Python and
  `{{ _("...") }}` / `{% trans %}` in templates, translated with gettext (Babel) into the
  language of each request. `swl.i18n_middleware` chooses it: the application's selector, the
  cookie `swl_lang`, `Accept-Language`, the first of `i18n.locales`. Applications add
  their catalogs with `swl.i18n.add_translations(path)`; `python -m swl.i18n_tool` extracts
  and compiles them. Filters `format_date`, `format_time`, `format_datetime`,
  `format_skeleton`, `format_number`, `format_timedelta` in the request's language.
- SWL's own texts (dialog, account and user screens, `swl.views.account` messages) in Dutch,
  German, French and Spanish (`swl/locale`).
- The example speaks English, Dutch, German and Spanish (a language switch in the top bar),
  and has private tasks: only their owner sees them, and their changes go to the owner's
  pages only (`signal_change(..., users=[owner])`).
- `SWL.lang`: the language of the request; `base.j2` uses it for `<html lang>` unless the
  template sets `lang`.

### Changed

- The example only accepts websockets of logged-in users.
- `base.j2` puts the texts for `swl.js` in the page (`<script id="swl-lang">`), in the
  page's language; the `lang` attribute of `swl-run.js` and the JSON files in
  `static/swl/lang/` are only used by pages without it (deprecated).
- New dependency: `babel`.
- `Dispatcher._listeners` is a dict (websocket to identity) instead of a list.
- The modal header (`swl/modal-content.j2`) is a grid: icon, title and close button on one
  row, the subtitle below the title, also using the width under the close button. A long
  subtitle no longer squeezes the close button. The header's children changed: the
  `swl-modal-heading` wrapper is gone; the icon is in `.swl-modal-icon`, the close button
  has `.swl-modal-close`.

## 5.2.0 (2026-10-30)

### Added

- `swl.endpoint(..., paths=fn)`: `/.routes` lists the paths `fn` returns (each as a static
  route) instead of the route's pattern, e.g. only the existing projects for `/{slug}`. `fn`
  gets the same arguments as the page function, may be async and is called on every request
  to `/.routes`.

### Changed

- `swl.routes_endpoint.collect_routes` is async and takes the request as its second argument.

## 5.1.0 (2026-10-30)

### Added

- A website, <https://seecr.github.io/swl/>, with the reference online and as a PDF. It lives
  in `site/` (Hugo) and is published to GitHub Pages after each release.
- Config option `routes.allowlist`: who may read `/.routes` (`swl.routes_route`), a list or a
  comma-separated string of IPs/CIDRs. Without it the `ROUTES_ALLOWLIST` environment variable
  is used, as before.

## 5.0.1 (2026-10-29)

Packaging, documentation and CI; no changes in behaviour.

### Changed

- The PyPI page has a clearer description, keywords and classifiers, and the README's links
  work there too.
- The htmx migration guide is removed.
- `swl/static/swl/seecr-logo-zonder.png` is removed; SWL didn't use it.
- Unused imports are removed from `swl.dispatcher`, `swl.passwd`, `swl.swl` and
  `swl.userbase`. Import names like `BaseUser`, `WebSocket` or `Config` from where they are
  defined (Starlette, `seecr_stdlib.config`), not through these modules.

### Added

- `SECURITY.md`: how to report a security problem.
- `python -m swl.test.run_js_tests` runs the JavaScript (QUnit) tests in headless Chromium.
- CI runs the JavaScript tests and flake8, besides the Python tests on Python 3.11 to 3.14.
- Each release also gets a GitHub release with its section of this changelog.

## 5.0.0 (2026-10-29)

SWL moves its browser side to [htmx 4](https://four.htmx.org). The Python API (actions,
`register()`, `swl.success()` / `swl.fail()`) stays the same, but templates and JavaScript have
to be converted.

SWL is now released under the MIT License (it was GPL v2 or later), and is published on
[GitHub](https://github.com/seecr/swl) and [PyPI](https://pypi.org/project/swl/).

### Breaking

- **htmx instead of SWL's own jQuery code.**
  - The `data-swl-*` attributes are replaced by `hx-*` attributes; `data-swl-validate` and
    `data-swl-on-changed` stay.
  - jQuery is no longer loaded.
  - `rehydrate.js` is gone, and `swl.js` no longer exports `hydrate`, `start_hydrating`,
    `rehydrate_placeholder`, `arguments_from_elem` and `swl_arguments_from_elem`.
- **The response is HTML plus headers instead of JSON.**
  - Hydrated content arrives as `<hx-partial>` elements, and the other instructions as an
    `HX-Trigger` header.
  - An empty response is `204`; `swl.fail()` is `422`.
  - Tests use `swl.test_utils.assert_success()` and `assert_fail()` instead of
    `response.json()`.
- **`hydrate()` data can no longer be an action url** that is fetched next. Return a placeholder
  in the HTML instead.
- **Placeholders post only their own values** (`hx-vals` and `hx-include`), not the fields inside
  or around them.
- **The modal, message dialog, toast and context menu are native HTML.** The modal and dialog
  are `<dialog>` elements; the toast and context menu are popovers. They no longer need
  Bootstrap's JavaScript.
  - `swl/modal-content.j2` uses `swl-modal-*` classes instead of Bootstrap's `modal-header` /
    `modal-body`.
  - JavaScript that listened to `shown.bs.modal` / `hidden.bs.modal` uses `swl-modal-shown` /
    the dialog's `close` event.
  - Put context menu items in a `<div class="swl-menu">`.
  - A page with its own Bootstrap modal markup (`<div id="swl-modal" class="modal">`) still
    works.
- **Web resources come from cdn.jsdelivr.net**, with integrity hashes: htmx 4.0.0, Bootstrap
  5.3.8 (was 5.3.0), Bootstrap Icons 1.13.1 (was 1.11.3), Tabler 1.6.1 and Bulma 1.0.4.
  - `urls.cdn` now defaults to `https://cdn.jsdelivr.net` (was `https://cdn.seecr.nl`).
  - `swl/resources/default-web-resources.json` is renamed to `bootstrap-web-resources.json`.
- **The account and user screens have a new layout.** They have captions above the fields, an
  avatar, and toasts after a change. An application that styled their old Bootstrap markup should
  check them.

### Added

- **Choice of CSS framework**: `ui.framework` is `"bootstrap"` (the default), `"tabler"`,
  `"bulma"` or `"swl"`.
  - `"swl"` uses SWL's own `swl-base.css`, with no framework at all.
  - The choice sets the web resources, and `SWL.ui`: CSS classes for inputs, buttons and tables
    in that framework.
  - `paths.resources` still replaces the resources with your own file.
- **Theme variables** (`--swl-accent`, `--swl-bg`, ...) for SWL's own parts. They follow
  Bootstrap's, Tabler's or Bulma's colours.
- **Layout classes in `swl.css`** that work with every framework: `swl-container`, `swl-nav`,
  `swl-columns`, `swl-card`, `swl-tabs`, `swl-stack`, `swl-row`, `swl-field`, `swl-list`,
  `swl-link`, `swl-menu` and more.
- **Light and dark colours**: `/static/swl/theme.js` with `swl_theme.set("light" | "dark" |
  "auto")`, for every framework.
- **`FrameworkCookieMiddleware`**: lets a visitor choose the framework with a cookie, for demos
  and style guides.
- **`placeholder()` macro** (`swl/placeholder.j2`) for elements that load and reload
  themselves.
- **`swl.success().trigger(event, **detail)`**: fire your own JavaScript event.
- **`data-swl-close`** on a button closes the modal. `swl/modal-content.j2` has an optional
  `modal_footer` block.
- **Deep links.**
  - `kickstart` now waits until the page's placeholders have loaded, so it can rebuild nested
    screens.
  - Its `kwargs` may be a dict and are escaped safely.
  - `doc/reference.md` explains deep links: `set_url` plus a page route.
- **An example application** (`example/`, a task list) with a guided walkthrough. Run it with
  `--framework swl | bootstrap | tabler | bulma`.
- **Documentation**: `README.md` and `doc/reference.md` (with debugging and troubleshooting).

### Fixed

- Failing requests (HTTP errors, network errors) are reported in SWL's dialog, never swapped into
  the page. A request that ends on a redirect, for example to the login page after the session
  expired, becomes a page load.
- A function called by name (`call`, `data-swl-validate`, the modal's `call`) that is missing or
  fails is reported, and does not stop the rest of the response.
- The context menu posts the element's values and the click position correctly.
- `open_modal(call=...)` runs the function once per opening.
- A second toast while the first is still showing no longer causes an error.
- `SWL.globals` referred to an attribute that does not exist.
