## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024, 2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

from pathlib import Path

import pytest
import argon2
import json

from .userbase import Userbase
from uuid import uuid1


@pytest.fixture
def tmp_userbase(tmp_path):
    return Userbase.for_testing(tmp_path)


def test_create(tmp_userbase):
    assert tmp_userbase.exists(username="john") is False
    tmp_userbase.create(username="john", password="smith")

    assert tmp_userbase.exists(username="john") is True


def test_admin_created(tmp_path, capfd):
    ub = Userbase.for_testing(tmp_path)
    assert ub.exists("admin") is False
    ub.ensure_admin()
    assert ub.exists("admin") is True
    out, err = capfd.readouterr()
    assert out.startswith("Admin password: ")


def test_admin_created_with_file(tmp_path):
    (tmp_path / "state").mkdir()

    ub = Userbase.for_testing(tmp_path)
    assert ub.exists("admin") is False

    file_path = tmp_path / "state" / "admin_bootstrap"
    assert not file_path.exists()

    ub.ensure_admin(file_path)
    assert ub.exists("admin") is True
    assert file_path.exists()

    file_contents = file_path.read_text()
    assert file_contents.startswith("Admin user created; initial password: ")
    assert len(file_contents) == len("Admin user created; initial password: ") + 16


def test_bad_usernames(tmp_userbase):
    bad_usernames = [
        "",
        "   ",
        "ad min",
        "ad\nmin",
        "ad\tmin",
        "../etc/passwd",
        "user/name",
        "user\\name",
    ]
    for bad_username in bad_usernames:
        with pytest.raises(ValueError):
            tmp_userbase.create(username=bad_username, password="smith")


def test_delete(tmp_userbase):
    assert tmp_userbase.exists(username="john") is False
    tmp_userbase.create(username="john", password="smith")
    assert tmp_userbase.exists(username="john") is True
    tmp_userbase.delete(username="john")
    assert tmp_userbase.exists(username="john") is False


def test_delete_admin_users(tmp_userbase):
    tmp_userbase.create(username="alice", password="wonderland", admin=True)
    assert tmp_userbase.exists(username="alice") is True
    assert not tmp_userbase.delete(username="alice")
    assert tmp_userbase.exists(username="alice") is True


def test_cannot_delete_admin(tmp_userbase):
    tmp_userbase.ensure_admin()
    assert tmp_userbase.exists(username="admin") is True
    tmp_userbase.delete(username="admin")
    assert tmp_userbase.exists(username="admin") is True


def test_ensure_admin_at_least_one_admin(tmp_userbase):
    admin = tmp_userbase.get(username="admin")
    assert admin is None
    tmp_userbase.create(username="alice", password="wonderland", admin=True)
    tmp_userbase.create(username="bob", password="builder", admin=False)
    users = tmp_userbase.all_users()
    assert [user["username"] for user in users if user["admin"]] == ["alice"]

    tmp_userbase.ensure_admin()
    users = tmp_userbase.all_users()
    assert [user["username"] for user in users if user["admin"]] == ["alice"]


def test_valid_password(tmp_userbase):
    assert tmp_userbase.valid_password(username="john", password="smith") is False
    tmp_userbase.create(username="john", password="smith")
    assert tmp_userbase.valid_password(username="john", password="smith") is True


def test_change_password(tmp_userbase):
    tmp_userbase.create(username="john", password="smith")
    assert tmp_userbase.valid_password(username="john", password="smith") is True

    tmp_userbase.change_password(username="john", password="jones")
    assert tmp_userbase.valid_password(username="john", password="smith") is False
    assert tmp_userbase.valid_password(username="john", password="jones") is True


def test_create_again(tmp_userbase):
    tmp_userbase.create(username="john", password="smith")
    user = tmp_userbase.get(username="john")
    assert user is not None

    with pytest.raises(ValueError):
        tmp_userbase.create(username="john", password="smith")


def test_put(tmp_userbase):
    tmp_userbase.create(username="john", password="smith")
    user = tmp_userbase.get(username="john")

    user["some_data"] = 12
    tmp_userbase.put(user)

    user2 = tmp_userbase.get(username="john")
    assert "some_data" in user2


def test_all_users(tmp_userbase):
    tmp_userbase.ensure_admin()
    all_users = tmp_userbase.all_users()
    assert all_users == [{"username": "admin", "admin": True}]

    tmp_userbase.create(username="john", password="smith")
    all_users = tmp_userbase.all_users()
    assert all_users == [
        {"username": "admin", "admin": True},
        {"username": "john", "admin": False},
    ]


def test_warning(tmp_path):
    users_path = Path(tmp_path) / "users"
    users_path.mkdir()
    ub = Userbase.for_testing(users_path)
    ub.create(username="john", password="smith")
    assert [user["username"] for user in ub.all_users()] == ["john"]

    with pytest.warns(DeprecationWarning):
        ubagain = Userbase.for_testing(tmp_path)
        assert [user["username"] for user in ubagain.all_users()] == ["john"]


def test_convert(tmp_path):
    users_path = Path(tmp_path) / "users"
    users_path.mkdir()
    hasher = argon2.PasswordHasher.from_parameters(argon2.profiles.CHEAPEST)
    admin_id = str(uuid1())
    users_path.joinpath("admin.json").write_text(
        json.dumps(
            {
                "username": "admin",
                "id": admin_id,
                "password": hasher.hash("something"),
                "admin": True,
                "some_data": 42,
            }
        )
    )
    john_id = str(uuid1())
    users_path.joinpath("john.json").write_text(
        json.dumps(
            {
                "username": "john",
                "id": john_id,
                "password": hasher.hash("smith"),
            }
        )
    )
    with pytest.warns(DeprecationWarning) as w:
        ubagain = Userbase.for_testing(users_path)
        admin = ubagain.get(username="admin")
        john = ubagain.get(username="john")
        assert admin.id == admin_id
        assert admin.admin is True
        assert admin.data["some_data"] == 42
        assert john.id == john_id

    assert json.loads(users_path.joinpath(f"{admin_id}.json").read_text()) == {
        "admin": True,
        "some_data": 42,
    }
    assert not users_path.joinpath("admin.json").exists()
