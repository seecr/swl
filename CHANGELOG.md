# Changelog

## Unreleased

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
