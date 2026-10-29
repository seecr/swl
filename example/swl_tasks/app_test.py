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

"""Tests for the example. They show how to test SWL actions: post to the action url and check
the response with the helpers from swl.test_utils."""

import json
import re

import pytest
from starlette.testclient import TestClient

from swl.test_utils import assert_fail, assert_success
from swl.userbase import Userbase

from swl_tasks.app import DEMO_PASSWORD, DEMO_USER, create_app


@pytest.fixture
def client(tmp_path):
    userbase = Userbase.for_testing(tmp_path / "users")  # fast password hashing for tests
    return TestClient(create_app(tmp_path, userbase=userbase))


def action(client, name):
    return client.app.state.swl.register(name)


def login(client):
    response = client.post(action(client, "login"), data={"username": DEMO_USER, "password": DEMO_PASSWORD})
    assert_success(response)
    assert response.headers["HX-Redirect"] == "/"


def partials(response):
    """The html per placeholder id in a response."""
    return dict(re.findall(r'<hx-partial hx-target="#([^"]+)" hx-swap="innerHTML">(.*?)</hx-partial>', response.text, re.S))


def test_page_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    response = client.get("/login")
    assert 'name="next" value="/"' in response.text

    response = client.post(action(client, "tasks_list"))
    assert response.status_code == 403

    response = client.post(action(client, "login"), data={"username": DEMO_USER, "password": "wrong"})
    assert_fail(response, "Invalid login credentials")

    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="tasks-list"' in response.text


def test_add_edit_toggle_delete(client):
    login(client)
    store = client.app.state.store

    # empty title
    assert_fail(client.post(action(client, "task_save"), data={"title": "  "}), "A task needs a title")

    # new task: form in the modal, then save
    response = client.post(action(client, "task_new"))
    assert assert_success(response)["swl-modal-open"]["calls"] == ["focus_title"]
    assert 'name="title"' in partials(response)["modal-content"]

    response = client.post(action(client, "task_save"), data={"title": "Write example", "notes": "for SWL"})
    [task] = store.find()
    assert assert_success(response) == {
        "swl-modal-close": {},
        "swl-rehydrate": {
            "placeholders": {"tasks-list": {"highlight": task.id}, "task-detail": {"highlight": task.id}}
        },
        "swl-toast": {"delay": 500},
    }
    assert partials(response) == {"toast-body": "Task saved"}

    # the list
    response = client.post(action(client, "tasks_list"), data={"highlight": task.id})
    events = assert_success(response)
    assert events["swl-call"] == {"calls": [{"method": "show_counts", "kwargs": {"open": 1, "done": 0}}]}
    html = partials(response)["tasks-list"]
    assert "Write example" in html and "task-highlight" in html
    assert response.headers["HX-Replace-Url"] == "/"

    # edit
    response = client.post(action(client, "task_edit"), data={"task_id": task.id})
    assert 'value="Write example"' in partials(response)["modal-content"]
    client.post(action(client, "task_save"), data={"task_id": task.id, "title": "Write the example", "notes": ""})
    assert store.get(task.id).title == "Write the example"

    # toggle
    assert_success(client.post(action(client, "task_toggle"), data={"task_id": task.id}))
    assert store.get(task.id).done is True

    assert [entry["what"] for entry in store.get(task.id).history] == ["Created", "Edited", "Marked as done"]

    # filters
    response = client.post(action(client, "tasks_list"), data={"q": "example", "status": "open"})
    assert "No tasks match the filter" in partials(response)["tasks-list"]
    assert response.headers["HX-Replace-Url"] == "/?q=example&status=open"

    # context menu
    response = client.post(action(client, "task_menu"), data={"task_id": task.id, "event_x": "10", "event_y": "20.5"})
    assert assert_success(response)["swl-contextmenu"] == {"x": 10, "y": 20}
    assert "Mark as open" in partials(response)["swl-contextmenu"]

    # delete
    response = client.post(action(client, "task_delete"), data={"task_id": task.id})
    assert assert_success(response)["swl-rehydrate"] == {"placeholders": {"tasks-list": {}, "task-detail": {}}}
    assert store.find() == []
    assert_fail(client.post(action(client, "task_delete"), data={"task_id": task.id}), "This task no longer exists")


def test_changes_are_signalled_over_the_websocket(client):
    login(client)
    with client.websocket_connect("/ws") as websocket:
        assert websocket.receive_json() == {"response": "pong"}
        client.post(action(client, "task_save"), data={"title": "Live"})
        assert websocket.receive_json() == {"response": "change", "obj": "tasks"}


def test_tasks_are_saved(tmp_path):
    from swl_tasks.store import TaskStore

    store = TaskStore(tmp_path / "tasks.json")
    task = store.add("Persist me", notes="please")
    store.toggle(task.id)
    assert json.loads((tmp_path / "tasks.json").read_text())[0]["done"] is True
    assert TaskStore(tmp_path / "tasks.json").get(task.id) == task


def test_select_a_task_and_switch_tabs(client):
    login(client)
    store = client.app.state.store
    task = store.add("Write tests", notes="for the tabs")
    other = store.add("Other task")

    # click a title: the task is shown on its first tab, remembered, put in the url, and the
    # list is reloaded to move the "selected" mark
    filters = {"q": "", "status": "all", "selected_task": "", "selected_tab": "details"}
    response = client.post(action(client, "task_detail"), data={**filters, "task": task.id})
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
        action(client, "task_detail"), data={**selected, "q": "write", "task": task.id, "tab": "history"}
    )
    assert assert_success(response) == {}
    assert "Created" in partials(response)["task-detail"]
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/history?q=write"

    # a rehydrate of the panel (only #filters posted) shows what is selected; unknown tab -> first tab
    response = client.post(action(client, "task_detail"), data={**selected, "selected_tab": "nonsense"})
    assert re.search(r'aria-selected="true"[^>]*>Details</button>', partials(response)["task-detail"], re.S)
    assert response.headers["HX-Replace-Url"] == f"/tasks/{task.id}/details"

    # the selected task is deleted (here or in another browser tab): say so and forget it
    store.delete(task.id)
    response = client.post(action(client, "task_detail"), data=selected)
    assert "This task no longer exists" in partials(response)["task-detail"]
    assert 'name="selected_task" value=""' in partials(response)["selection"]
    assert response.headers["HX-Replace-Url"] == "/"
    assert other.id in str(store.find())


def test_reload_renders_the_same_screen(client):
    login(client)
    task = client.app.state.store.add("Deep link me")

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
    [("swl", "swl-base.css", 'class="primary"'), ("bootstrap", "bootstrap.min.css", 'class="btn btn-primary"'),
     ("tabler", "tabler.min.css", 'class="btn btn-primary"'),
     ("bulma", "bulma.min.css", 'class="button is-primary"')],
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
