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

"""Tests for the example. They show how to test SWL actions: post to the action url and
check the response with the helpers from swl.test_utils."""

import json
import re

import pytest
from starlette.testclient import TestClient
from swl_tasks.app import DEMO_PASSWORD, DEMO_USER, create_app

from swl.test_utils import assert_fail, assert_success
from swl.userbase import Userbase


@pytest.fixture
def client(tmp_path):
    userbase = Userbase.for_testing(tmp_path / "users")  # fast password hashing for tests
    return TestClient(create_app(tmp_path, userbase=userbase))


def action(client, name):
    return client.app.state.swl.register(name)


def login(client):
    response = client.post(
        action(client, "login"),
        data={"username": DEMO_USER, "password": DEMO_PASSWORD},
    )
    assert_success(response)
    assert response.headers["HX-Redirect"] == "/"


def partials(response):
    """The html per placeholder id in a response."""
    return dict(
        re.findall(
            r'<hx-partial hx-target="#([^"]+)" hx-swap="innerHTML">(.*?)</hx-partial>',
            response.text,
            re.S,
        )
    )


def test_page_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    response = client.get("/login")
    assert 'name="next" value="/"' in response.text

    response = client.post(action(client, "tasks_list"))
    assert response.status_code == 403

    response = client.post(
        action(client, "login"), data={"username": DEMO_USER, "password": "wrong"}
    )
    assert_fail(response, "Invalid login credentials")

    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="tasks-list"' in response.text


def test_add_edit_toggle_delete(client):
    login(client)
    store = client.app.state.store

    # empty title
    assert_fail(
        client.post(action(client, "task_save"), data={"title": "  "}),
        "A task needs a title",
    )

    # new task: form in the modal, then save
    response = client.post(action(client, "task_new"))
    assert assert_success(response)["swl-modal-open"]["calls"] == ["focus_title"]
    assert 'name="title"' in partials(response)["modal-content"]

    response = client.post(
        action(client, "task_save"), data={"title": "Write example", "notes": "for SWL"}
    )
    [task] = store.find("demo")
    assert assert_success(response) == {
        "swl-modal-close": {},
        "swl-rehydrate": {
            "placeholders": {
                "tasks-list": {"highlight": task.id},
                "task-detail": {"highlight": task.id},
            }
        },
        "swl-toast": {"delay": 500},
    }
    assert partials(response) == {"toast-body": "Task saved"}

    # the list
    response = client.post(action(client, "tasks_list"), data={"highlight": task.id})
    events = assert_success(response)
    assert events["swl-call"] == {
        "calls": [
            {"method": "show_counts", "kwargs": {"open": 1, "text": "1 open / 0 done"}}
        ]
    }
    html = partials(response)["tasks-list"]
    assert "Write example" in html and "task-highlight" in html
    assert response.headers["HX-Replace-Url"] == "/"

    # edit
    response = client.post(action(client, "task_edit"), data={"task_id": task.id})
    assert 'value="Write example"' in partials(response)["modal-content"]
    client.post(
        action(client, "task_save"),
        data={"task_id": task.id, "title": "Write the example", "notes": ""},
    )
    assert store.get(task.id, "demo").title == "Write the example"

    # toggle
    assert_success(client.post(action(client, "task_toggle"), data={"task_id": task.id}))
    assert store.get(task.id, "demo").done is True

    assert [entry["what"] for entry in store.get(task.id, "demo").history] == [
        "Created",
        "Edited",
        "Marked as done",
    ]

    # filters
    response = client.post(
        action(client, "tasks_list"), data={"q": "example", "status": "open"}
    )
    assert "No tasks match the filter" in partials(response)["tasks-list"]
    assert response.headers["HX-Replace-Url"] == "/?q=example&status=open"

    # context menu
    response = client.post(
        action(client, "task_menu"),
        data={"task_id": task.id, "event_x": "10", "event_y": "20.5"},
    )
    assert assert_success(response)["swl-contextmenu"] == {"x": 10, "y": 20}
    assert "Mark as open" in partials(response)["swl-contextmenu"]

    # delete
    response = client.post(action(client, "task_delete"), data={"task_id": task.id})
    assert assert_success(response)["swl-rehydrate"] == {
        "placeholders": {"tasks-list": {}, "task-detail": {}}
    }
    assert store.find("demo") == []
    assert_fail(
        client.post(action(client, "task_delete"), data={"task_id": task.id}),
        "This task no longer exists",
    )


def test_changes_are_signalled_over_the_websocket(client):
    login(client)
    with client.websocket_connect("/ws") as websocket:
        assert websocket.receive_json() == {"response": "pong"}
        client.post(action(client, "task_save"), data={"title": "Live"})
        assert websocket.receive_json() == {"response": "change", "obj": "tasks"}


def test_tasks_are_saved(tmp_path):
    from swl_tasks.store import TaskStore

    store = TaskStore(tmp_path / "tasks.json")
    task = store.add("Persist me", "demo", notes="please")
    store.toggle(task.id)
    assert json.loads((tmp_path / "tasks.json").read_text())[0]["done"] is True
    assert TaskStore(tmp_path / "tasks.json").get(task.id, "demo") == task


def test_select_a_task_and_switch_tabs(client):
    login(client)
    store = client.app.state.store
    task = store.add("Write tests", "demo", notes="for the tabs")
    other = store.add("Other task", "demo")

    # click a title: the task is shown on its first tab, remembered, put in the url, and
    # the list is reloaded to move the "selected" mark
    filters = {
        "q": "",
        "status": "all",
        "selected_task": "",
        "selected_tab": "details",
    }
    response = client.post(
        action(client, "task_detail"), data={**filters, "task": task.id}
    )
    events = assert_success(response)
    html = partials(response)
    assert "for the tabs" in html["task-detail"]
    assert f'name="selected_task" value="{task.id}"' in html["selection"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/details"
    assert events == {"swl-rehydrate": {"placeholders": {"tasks-list": {}}}}

    # the list marks the selected task
    selected = {**filters, "selected_task": task.id}
    response = client.post(action(client, "tasks_list"), data=selected)
    assert "task-selected" in partials(response)["tasks-list"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/details"

    # another tab of the same task: no list reload; filters stay in the url
    response = client.post(
        action(client, "task_detail"),
        data={**selected, "q": "write", "task": task.id, "tab": "history"},
    )
    assert assert_success(response) == {}
    assert "Created" in partials(response)["task-detail"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/history?q=write"

    # a rehydrate of the panel (only #filters posted) shows what is selected; unknown tab
    # -> first tab
    response = client.post(
        action(client, "task_detail"), data={**selected, "selected_tab": "nonsense"}
    )
    assert re.search(
        r'aria-selected="true"[^>]*>Details</button>',
        partials(response)["task-detail"],
        re.S,
    )
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/details"

    # the selected task is deleted (here or in another browser tab): say so and forget it
    store.delete(task.id)
    response = client.post(action(client, "task_detail"), data=selected)
    assert "This task no longer exists" in partials(response)["task-detail"]
    assert 'name="selected_task" value=""' in partials(response)["selection"]
    assert response.headers["HX-Replace-Url"] == "/"
    assert other.id in str(store.find("demo"))


def test_the_tree(client):
    login(client)
    store = client.app.state.store
    one = store.add("One", "demo")
    two = store.add("Two <b>", "demo", private=True)
    three = store.add("Three", "demo")
    store.toggle(three.id)

    # "Tree" in the filters: the placeholder gets the tree element, and tree_init fills it
    response = client.post(
        action(client, "tasks_list"),
        data={"view": "tree", "status": "all", "selected_task": one.id},
    )
    events = assert_success(response)
    assert 'id="task-tree"' in partials(response)["tasks-list"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{one.id}/details?view=tree"
    show_counts, tree_init = events["swl-call"]["calls"]
    assert show_counts["method"] == "show_counts"
    assert tree_init["method"] == "tree_init"
    kwargs = tree_init["kwargs"]
    assert kwargs["tree_id"] == "task-tree"
    assert kwargs["data_url"] == action(client, "task_tree_data")
    assert kwargs["params"] == {"q": "", "status": "all"}
    assert kwargs["selected"] == one.id and kwargs["notify"] is False
    assert kwargs["dnd"] == "any"

    # its nodes: the statuses, with the tasks in them
    response = client.post(action(client, "task_tree_data"), data={"node": "#"})
    assert response.json() == [
        {
            "id": "status-open",
            "text": "Open (2)",
            "parent": "#",
            "icon": "bi bi-circle",
            "state": {"opened": True},
            "type": "status",
            "data": {"draggable": False},
        },
        {
            "id": one.id,
            "text": "One",
            "parent": "status-open",
            "icon": "bi bi-card-text",
            "type": "task",
        },
        {
            "id": two.id,
            "text": "Two <b>",  # as text: tree.js does not show it as HTML
            "parent": "status-open",
            "icon": "bi bi-lock",
            "type": "task",
        },
        {
            "id": "status-done",
            "text": "Done (1)",
            "parent": "#",
            "icon": "bi bi-check-circle",
            "state": {"opened": True},
            "type": "status",
            "data": {"draggable": False},
        },
        {
            "id": three.id,
            "text": "Three",
            "parent": "status-done",
            "icon": "bi bi-card-text",
            "type": "task",
        },
    ]
    response = client.post(
        action(client, "task_tree_data"), data={"node": "#", "status": "done", "q": "x"}
    )
    assert response.json() == [
        {
            "id": "status-done",
            "text": "Done (0)",
            "parent": "#",
            "icon": "bi bi-check-circle",
            "state": {"opened": True},
            "type": "status",
            "data": {"draggable": False},
        }
    ]

    # a click on a task: shown on the right (no list reload: the tree shows the selection)
    response = client.post(
        action(client, "task_tree_select"),
        data={"node": two.id, "q": "", "status": "all"},
    )
    assert assert_success(response) == {}
    assert "Two &lt;b&gt;" in partials(response)["task-detail"]
    assert f'name="selected_task" value="{two.id}"' in partials(response)["selection"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{two.id}/details?view=tree"
    # a click on a status: nothing
    response = client.post(
        action(client, "task_tree_select"), data={"node": "status-open"}
    )
    assert response.status_code == 204

    # drag "Two" above "One"
    with client.websocket_connect("/ws") as websocket:
        assert websocket.receive_json() == {"response": "pong"}
        response = client.post(
            action(client, "task_tree_move"),
            data={
                "node": two.id,
                "parent": "status-open",
                "position": "0",
                "old_parent": "status-open",
                "old_position": "1",
            },
        )
        assert_success(response)
        assert websocket.receive_json() == {"response": "change", "obj": "tasks"}
    assert [t.title for t in store.find("demo")] == ["Two <b>", "One", "Three"]

    # drag "One" into Done, after "Three"; and back to Open, at the end
    client.post(
        action(client, "task_tree_move"),
        data={"node": one.id, "parent": "status-done", "position": "1"},
    )
    assert [t.title for t in store.find("demo", status="done")] == ["Three", "One"]
    assert store.get(one.id, "demo").history[-1]["what"] == "Marked as done"
    client.post(
        action(client, "task_tree_move"),
        data={"node": one.id, "parent": "status-open", "position": "1"},
    )
    assert [t.title for t in store.find("demo")] == ["Two <b>", "One", "Three"]

    # refused: the tree reloads itself (tree.js)
    assert_fail(
        client.post(
            action(client, "task_tree_move"),
            data={"node": one.id, "parent": two.id, "position": "0"},
        ),
        "A task can only go into Open or Done",
    )
    assert_fail(
        client.post(
            action(client, "task_tree_move"),
            data={"node": "gone", "parent": "status-open", "position": "0"},
        ),
        "This task no longer exists",
    )
    assert_fail(
        client.post(
            action(client, "task_tree_move"),
            data={"node": one.id, "parent": "status-open", "position": "x"},
        ),
        "Invalid position",
    )

    # a reload shows the tree again, with jstree loaded
    html = client.get(f"/tasks/{one.id}/details?view=tree").text
    assert '<option value="tree" selected>' in html
    assert "jstree.min.js" in html and "/static/swl/tree.js" in html


def test_moving_with_a_filter_and_other_users(tmp_path):
    from swl_tasks.store import TaskStore

    store = TaskStore()
    store.add("apple", "demo")
    store.add("secret", "other", private=True)
    b = store.add("banana", "demo")
    c = store.add("apple pie", "demo")
    # with search text "apple" the tree shows [apple, apple pie]; move "apple pie" first
    store.move(c.id, "demo", done=False, position=0, q="apple")
    assert [t.title for t in store.find("demo")] == ["apple pie", "apple", "banana"]
    assert [t.title for t in store.find("other")] == [
        "apple pie",
        "apple",
        "secret",
        "banana",
    ]
    # to an empty Done
    store.move(b.id, "demo", done=True, position=0)
    assert [t.title for t in store.find("demo", status="done")] == ["banana"]


def test_reload_renders_the_same_screen(client):
    login(client)
    task = client.app.state.store.add("Deep link me", "demo")

    response = client.get(f"/tasks/{task.id}/history?q=deep&status=open")
    assert response.status_code == 200
    html = response.text
    assert f'name="selected_task" value="{task.id}"' in html
    assert 'name="selected_tab" value="history"' in html
    assert 'value="deep"' in html and '<option value="open" selected>' in html
    # the detail panel is rendered into the page: no request needed after a reload
    detail = html[html.index('id="task-detail"'):]
    assert "Created" in detail[: detail.index("</main>")]

    # nonsense in the url gives the start screen, not an error
    response = client.get("/tasks/doesnotexist/whatever")
    assert response.status_code == 200
    assert "This task no longer exists" in response.text
    assert 'name="selected_task" value=""' in response.text


@pytest.mark.parametrize(
    "framework, css, primary",
    [
        ("swl", "swl-base.css", 'class="primary"'),
        ("bootstrap", "bootstrap.min.css", 'class="btn btn-primary"'),
        ("tabler", "tabler.min.css", 'class="btn btn-primary"'),
        ("bulma", "bulma.min.css", 'class="button is-primary"'),
    ],
)
def test_the_page_works_with_each_framework(tmp_path, framework, css, primary):
    userbase = Userbase.for_testing(tmp_path / "users")
    client = TestClient(create_app(tmp_path, userbase=userbase, framework=framework))
    login(client)
    html = client.get("/").text
    assert css in html and f'data-swl-framework="{framework}"' in html
    assert primary in html  # the "New task" button


def test_the_framework_switch_is_a_cookie(client):
    login(client)
    assert '<option value="swl" selected>' in client.get("/").text
    client.cookies.set("swl_framework", "bulma")
    html = client.get("/").text
    assert "bulma.min.css" in html and '<option value="bulma" selected>' in html
    assert 'class="button is-primary"' in html
    # actions render with the chosen framework too
    response = client.post(action(client, "show_account"))
    assert 'class="input"' in response.text
    client.cookies.set("swl_framework", "nonsense")
    assert '<option value="swl" selected>' in client.get("/").text


def second_user(client, userbase, username="alex", password="alex-password"):
    """Another user, logged in with a client of their own (same app, same event loop)."""
    userbase.create(username, password)
    other = TestClient(client.app)
    other.portal = client.portal
    response = other.post(
        action(other, "login"), data={"username": username, "password": password}
    )
    assert_success(response)
    return other


@pytest.fixture
def two_users(tmp_path):
    userbase = Userbase.for_testing(tmp_path / "users")
    with TestClient(create_app(tmp_path, userbase=userbase)) as client:
        login(client)
        yield client, second_user(client, userbase)


def test_private_tasks(two_users):
    demo, alex = two_users
    store = demo.app.state.store

    assert_success(demo.post(action(demo, "task_save"), data={"title": "Shared"}))
    assert_success(
        demo.post(action(demo, "task_save"), data={"title": "Secret", "private": "on"})
    )
    [secret] = [task for task in store.find("demo") if task.title == "Secret"]
    assert secret.private and secret.owner == "demo"

    def titles(client):
        return partials(client.post(action(client, "tasks_list")))["tasks-list"]

    assert "Secret" in titles(demo) and "Shared" in titles(demo)
    assert "Secret" not in titles(alex) and "Shared" in titles(alex)
    assert_fail(
        alex.post(action(alex, "task_toggle"), data={"task_id": secret.id}),
        "This task no longer exists",
    )
    page = alex.get(f"/tasks/{secret.id}").text  # a link to it
    assert "This task no longer exists" in page and "Secret" not in page


def test_private_changes_reach_only_the_owner(two_users):
    demo, alex = two_users
    assert_success(demo.post(action(demo, "task_save"), data={"title": "Shared"}))
    assert_success(
        demo.post(action(demo, "task_save"), data={"title": "Secret", "private": "on"})
    )
    store = demo.app.state.store
    [shared] = [task for task in store.find("demo") if task.title == "Shared"]
    [secret] = [task for task in store.find("demo") if task.title == "Secret"]

    with (
        demo.websocket_connect("/ws") as demo_ws,
        alex.websocket_connect("/ws") as alex_ws,
    ):
        assert demo_ws.receive_json() == alex_ws.receive_json() == {"response": "pong"}

        # a private task: only demo's pages hear about it
        assert_success(
            demo.post(action(demo, "task_toggle"), data={"task_id": secret.id})
        )
        assert demo_ws.receive_json() == {"response": "change", "obj": "tasks"}

        # a shared one: everyone. alex's first message is this one, not the private one
        assert_success(
            demo.post(action(demo, "task_toggle"), data={"task_id": shared.id})
        )
        assert demo_ws.receive_json() == {"response": "change", "obj": "tasks"}
        assert alex_ws.receive_json() == {"response": "change", "obj": "tasks"}

        # sharing a private task (or making a shared one private) concerns everyone
        assert_success(
            demo.post(
                action(demo, "task_save"),
                data={"task_id": secret.id, "title": "Secret"},
            )
        )
        assert alex_ws.receive_json() == {"response": "change", "obj": "tasks"}


def test_only_the_owner_makes_a_task_private(two_users):
    demo, alex = two_users
    assert_success(demo.post(action(demo, "task_save"), data={"title": "Shared"}))
    [shared] = demo.app.state.store.find("demo")
    assert_fail(
        alex.post(
            action(alex, "task_save"),
            data={"task_id": shared.id, "title": "Mine now", "private": "on"},
        ),
        "Only its owner can make a task private",
    )


def test_languages(client):
    login(client)
    dutch = {"accept-language": "nl-NL,nl;q=0.9,en;q=0.5"}
    page = client.get("/", headers=dutch).text
    assert 'lang="nl"' in page
    assert "Nieuwe taak" in page  # the example's own text
    assert '"confirm": "Bevestigen"' in page  # SWL's texts for swl.js

    assert_fail(
        client.post(action(client, "task_save"), data={"title": ""}, headers=dutch),
        "Een taak heeft een titel nodig",
    )
    client.cookies["swl_lang"] = "es"  # the language switch wins over the browser
    page = client.get("/", headers=dutch).text
    assert 'lang="es"' in page and "Nueva tarea" in page
    client.cookies["swl_lang"] = "de"
    response = client.post(action(client, "tasks_list"))
    assert partials(response)  # renders
    events = assert_success(response)
    assert events["swl-call"]["calls"][0]["kwargs"]["text"] == "0 offen / 0 erledigt"


@pytest.mark.parametrize("language", ["nl", "de", "es"])
def test_translations_are_complete_and_compiled(language):
    """After changing texts: python -m swl.i18n_tool extract|update|compile swl_tasks."""
    from pathlib import Path

    from babel.messages.pofile import read_po
    from babel.support import Translations

    locale = Path(__file__).parent / "locale"
    with open(locale / "messages.pot", "rb") as f:
        template = read_po(f)
    with open(locale / language / "LC_MESSAGES" / "messages.po", "rb") as f:
        catalog = read_po(f, locale=language)
    compiled = Translations.load(locale, [language], "messages")
    for message in template:
        if message.id:
            translated = catalog.get(message.id)
            assert translated is not None and translated.string, message.id
            assert compiled.gettext(message.id) == translated.string, message.id
