## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

from swl.test_utils import (
    assert_fail,
    assert_success,
    environment,
    login_user,
    logout_user,
)
from swl.views import account


async def test_user_create(environment):
    client, swl, userbase = environment

    logout_user(client)

    # No user logged in
    response = client.post(
        swl.register("user_create"),
        data={"username": "jane", "password": "secret123"},
    )
    assert response.status_code == 403

    # Regular user logged in
    userbase.create("john", "secret123")
    login_user(client, "john", "secret123")

    response = client.post(
        swl.register("user_create"),
        data={"username": "jane", "password": "secret123"},
    )
    assert_fail(response, "Unauthorized; only admin-users can create users")

    # Admin logged in
    login_user(client, "admin", "admin_password")

    response = client.post(
        swl.register("user_create"),
        data={"username": "Bo", "password": "secret123"},
    )
    assert_fail(response, "Username invalid; longer than 3 character and no spaces")

    response = client.post(
        swl.register("user_create"),
        data={"username": "Jane Doe", "password": "secret123"},
    )
    assert_fail(response, "Username invalid; longer than 3 character and no spaces")

    assert not userbase.exists(username="Jane")
    response = client.post(
        swl.register("user_create"),
        data={"username": "Jane", "password": "secret123"},
    )
    assert assert_success(response) == {
        "swl-reset-form": {},
        "swl-rehydrate": {"placeholders": {"placeholder-users_list": {}}},
        "swl-toast": {"delay": 500},
    }
    assert userbase.exists(username="Jane")

    response = client.post(
        swl.register("user_create"),
        data={"username": "Jane", "password": "secret123"},
    )
    assert_fail(response, "Username already in use")

    response = client.post(
        swl.register("user_create"),
        data={"username": "jane", "password": "secret123"},
    )
    assert_fail(response, "Username already in use")


async def test_user_delete(environment):
    client, swl, userbase = environment

    logout_user(client)

    # No user
    response = client.post(swl.register("user_delete"), data={"username": "Jane"})
    assert response.status_code == 403

    # Regular user logged in
    userbase.create("john", "secret123")
    login_user(client, "john", "secret123")

    # Delete for admin users only
    response = client.post(swl.register("user_delete"), data={"username": "Jane"})
    assert_fail(response, "Unauthorized; only admin-users can delete users")

    # Switch to admin, create and delete user
    login_user(client, "admin", "admin_password")

    response = client.post(
        swl.register("user_create"),
        data={"username": "Jane", "password": "secret123"},
    )
    assert userbase.exists(username="Jane")

    response = client.post(swl.register("user_delete"), data={"username": "Jane"})
    assert assert_success(response) == {
        "swl-rehydrate": {"placeholders": {"placeholder-users_list": {}}},
    }
    assert not userbase.exists(username="Jane")

    # Delete user that doesn't exist
    response = client.post(swl.register("user_delete"), data={"username": "Jane"})
    assert_fail(response, "No such user")

    response = client.post(swl.register("user_delete"), data={"username": "admin"})
    assert_fail(response, "Deleting own user not allowed")


async def test_user_make_admin(environment):
    client, swl, userbase = environment

    response = client.post(
        swl.register("user_create"),
        data={"username": "Bob", "password": "secret123"},
    )
    assert userbase.exists(username="Bob")

    logout_user(client)
    login_user(client, "bob", "secret123")

    # Set admin is for admin users only
    response = client.post(swl.register("user_set_admin"), data={"username": "Jane"})
    assert_fail(response, "Unauthorized; only admin-users can set admin on users")


async def test_user_make_admin_not_on_self(environment):
    client, swl, userbase = environment

    userbase.create(username="Bob", password="secret123", admin=True)
    userbase.create(username="Wendy", password="secret124", admin=True)

    assert (userbase.get("Bob")).admin is True
    assert (userbase.get("Wendy")).admin is True

    logout_user(client)
    login_user(client, "bob", "secret123")

    response = client.post(swl.register("user_set_admin"), data={"username": "Wendy"})
    assert_success(response)
    assert (userbase.get("Wendy")).admin is False

    response = client.post(swl.register("user_set_admin"), data={"username": "Bob"})
    assert_fail(response)
    assert (userbase.get("Bob")).admin is True


async def test_change_password(environment):
    client, swl, userbase = environment
    client.post(
        swl.register("user_create"),
        data={"username": "Bob", "password": "secret123"},
    )
    assert userbase.exists(username="Bob")

    logout_user(client)
    login_user(client, "bob", "secret123")

    client.post(
        swl.register("change_password"),
        data={
            "username": "bob",
            "current_password": "secret123",
            "new_password": "new_secret123",
            "new_password_repeat": "new_secret123",
        },
    )
    logout_user(client)
    login_user(client, "bob", "new_secret123")


async def test_change_password_other_only_for_admin(environment):
    client, swl, userbase = environment
    response = client.post(
        swl.register("user_create"),
        data={"username": "Bob", "password": "secret123"},
    )
    response = client.post(
        swl.register("user_create"),
        data={"username": "Wendy", "password": "very_secret"},
    )
    assert userbase.exists(username="Bob")
    assert userbase.exists(username="Wendy")

    logout_user(client)
    login_user(client, "bob", "secret123")

    response = client.post(
        swl.register("change_password"),
        data={
            "username": "wendy",
            "current_password": "very_secret",
            "new_password": "new_secret123",
            "new_password_repeat": "new_secret123",
        },
    )
    assert_fail(response, "Unauthorized; only admin-users can change other users passwords")


async def test_login_next(environment):
    client, swl, userbase = environment

    userbase.create(username="Bob", password="secret123", admin=True)

    logout_user(client)

    response = client.post("/login", data={"username": "bob", "password": "secret123"})
    assert_success(response)
    assert response.headers["HX-Redirect"] == "/"

    logout_user(client)
    response = client.post(
        "/login", data={"username": "bob", "password": "secret123", "next": "/admin"}
    )
    assert_success(response)
    assert response.headers["HX-Redirect"] == "/admin"


def _rows(html):
    """username -> (admin switch disabled, delete button disabled), from users_list.j2"""
    import re

    rows = {}
    for item in re.findall(r"<li>(.*?)</li>", html, re.S):
        username = re.search(r'name="username" value="([^"]+)"', item).group(1)
        switch = re.search(r'<input class="swl-switch[^>]*>', item, re.S).group(0)
        button = re.search(r"<button[^>]*>", item, re.S).group(0)
        rows[username] = ("disabled" in switch, "disabled" in button)
    return rows


async def test_account_views_render(environment):
    client, swl, userbase = environment

    response = client.post(swl.register("show_account"))
    html = response.text
    assert "My account" in html and "admin · Administrator" in html
    assert 'name="current_password"' in html and 'name="new_password_repeat"' in html

    response = client.post(swl.register("users_show"))
    assert "Add a user" in response.text

    # admin: own row locked, other admins cannot be deleted, users can
    userbase.create("bob", "secret123", admin=True)
    response = client.post(swl.register("users_list"), data={"placeholder": "placeholder-users_list"})
    assert _rows(response.text) == {
        "admin": (True, True),
        "bob": (False, True),
        "user": (False, False),
    }
    assert "3 users" in response.text

    # a regular user sees the list, but cannot change anything
    logout_user(client)
    login_user(client, "user", "user_password")
    response = client.post(swl.register("users_show"))
    assert "Add a user" not in response.text and "Only administrators" in response.text
    response = client.post(swl.register("users_list"), data={"placeholder": "placeholder-users_list"})
    assert set(_rows(response.text).values()) == {(True, True)}


async def test_change_password_confirms(environment):
    client, swl, userbase = environment
    response = client.post(
        swl.register("change_password"),
        data={
            "username": "admin",
            "current_password": "admin_password",
            "new_password": "new_password",
            "new_password_repeat": "new_password",
        },
    )
    assert assert_success(response) == {"swl-reset-form": {}, "swl-toast": {"delay": 500}}
