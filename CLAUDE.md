# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# SWL (Seecr Web Lib)

Python library for interactive web apps: Starlette on the server, Jinja templates, htmx 4 in the
browser. MIT license. Maintained by Seecr (Johan Jonkers, Thijs Janssen).

## State of the project

- The browser side is htmx 4 (it was jQuery with `data-swl-*` attributes up to 4.3.0; a breaking
  change).
- SWL's modal/dialog are native `<dialog>`, toast and context menu are popovers, styled by
  `swl.css` with `--swl-*` variables; SWL needs no framework JavaScript. `"ui.framework"`:
  "bootstrap" (default), "tabler" (Bootstrap-based), "bulma" or "swl" (SWL's own `swl-base.css`,
  no framework) picks the web resources and `SWL.ui` (classes for inputs/buttons, see
  `swl/frameworks.py`). Layout classes (swl-nav, swl-columns, swl-card, swl-tabs) live in swl.css.
  The example runs with each: `python -m swl_tasks --framework bulma`.
  Pico CSS was considered and rejected (no longer maintained).

## Where things are

- `swl/swl.py`, `swl/actions.py`: app setup, action registration (`__actions__`, `register(name)`
  gives `/action/<md5>` urls; actions need a logged-in user unless `authenticated=False`).
- `swl/responses.py`: `swl.success()` / `swl.fail()` builder. Output = HTML with `<hx-partial>`
  elements (from `hydrate`) + an `HX-Trigger` header with SWL events (`swl-call`, `swl-rehydrate`,
  `swl-modal-open/-close`, `swl-contextmenu`, `swl-toast`, `swl-reset-form`, `swl-error`, ...),
  `HX-Redirect`, `HX-Replace-Url`. Empty response = 204, fail = 422 (+ `HX-Reswap: none`).
- `swl/static/swl/swl.js`: browser side (event handlers, dialogs via `swl.ui`, `swl_action`,
  `swl.rehydrate`, `swl.kickstart`, toasts); `swl-run.js` boots it; `websocket.js` = live updates
  (`data-swl-on-changed` placeholders reload when the dispatcher signals a change).
- `swl/templates/swl/`: `base.j2` (loads htmx + htmx-config meta), `placeholder.j2` (macro),
  `kickstart.j2`, `modal-content.j2`, account/users views (`swl/views/account.py`).
- `swl/resources/<framework>-web-resources.json`: CDN scripts/styles per framework, all from
  cdn.jsdelivr.net with SRI hashes (htmx is `htmx.org@4.0.0`); `web_resources.py` loads them.
- `swl/test_utils.py`: `assert_success(response)` (returns the events), `assert_fail(response, msg)`.
- `doc/reference.md`: full reference (deep links, tabs, debugging).
- `site/`: the website (Hugo), published to GitHub Pages by `.github/workflows/pages.yml` after
  each release; `make` in `site/` builds it and the reference PDF (pandoc + Typst,
  template `site/pdf/reference.typ`). Not part of the package.
- `example/`: task-list example app (`swl_tasks`), README walks one click end to end.
  Run: `pip install -e example && python -m swl_tasks`, login demo / demo-password.

## Key conventions (htmx 4 specifics that bite)

- Attributes only inherit when written as `hx-vals:inherited` / `hx-confirm:inherited`.
- Non-form elements (placeholders, links) post only `hx-vals` + `hx-include`, plus `placeholder=<id>`.
- `HX-Trigger` events fire after the swap; the source may be detached, so listen on `document`.
- Recipes for rehydrate live on the element (`hx-post` + `hx-vals`), not in sessionStorage.
- Deep links: actions call `set_url(...)`, the page route renders that screen; `kickstart` only for
  state only an action can produce (it waits until placeholders settle: 100 ms quiet, max 5 s).
- Values from users/urls into `hx-vals` or kickstart: always `|tojson`.
- Bootstrap tabs: `hx-trigger="show.bs.tab"`, plus `load, ` on the initially active tab. Without
  Bootstrap: `<nav class="swl-tabs">` with `aria-selected` buttons (see `doc/reference.md`).

## Testing

- Python: `pytest swl example/swl_tasks` (tests are `*_test.py` next to the code; needs
  `pip install -e . -e example/`). pytest runs with `-n5` (xdist) and `asyncio_mode = auto` from
  `pyproject.toml`; for one test use `pytest -n0 swl/responses_test.py::test_name`.
- JavaScript: QUnit tests in `swl/test/js-test/swl.test.js`, served by `python -m swl.test.server`
  (open http://localhost:8000/). Headless: `python -m swl.test.run_js_tests` (needs `playwright`
  and `python -m playwright install chromium`; exits 1 on a failure).
- Style: flake8 (`.flake8`, max line length 90, wrap by hand, no formatter), isort with the black
  profile. CI (`.github/workflows/test.yml`) runs pytest on 3.11-3.14, the JS tests and flake8.

## Working agreements

- Python >= 3.11; all dependencies come from PyPI. `env/` is a local virtualenv, ignored.
- Versions come from git tags via `setuptools_scm` (tags like `5.0.0`); `swl/_version.py` is
  generated and git-ignored. Pushing a version tag to GitHub publishes that version to PyPI
  and makes a GitHub release from its CHANGELOG section (`.github/workflows/publish.yml`), and
  PyPI never accepts a version twice. Don't push tags
  unless asked. `.github/workflows/test.yml` runs the tests on every push.
- Never push or publish to PyPI; that is the maintainers' decision. Commit messages are prefixed
  `JJ: `. No `Claude-Session:` lines in commit messages.
- Keep changes on a branch; report behaviour changes and anything left undone.
