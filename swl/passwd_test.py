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

from pathlib import Path

import pytest

from .passwd import Passwd
from uuid import UUID, uuid1

from seecr_testtools import anything

import json
import argon2


@pytest.fixture
def tmp_passwd(tmp_path):
    return Passwd.for_testing(tmp_path / "passwd")


def test_create_user(tmp_passwd):
    assert tmp_passwd.has_user(username="john") is False
    tmp_passwd.create_user(username="john", password="smith")

    assert tmp_passwd.has_user(username="john") is True
    assert tmp_passwd.has_user(username="John") is True

    john = tmp_passwd.get_user(username="john")
    john2 = tmp_passwd.get_user(username="John")
    assert UUID(john.id) == UUID(john2.id)


def test_create_user_once(tmp_passwd):
    assert tmp_passwd.has_user(username="john") is False
    tmp_passwd.create_user(username="john", password="smith")

    assert tmp_passwd.has_user(username="john") is True
    with pytest.raises(ValueError):
        tmp_passwd.create_user(username="john", password="smith")


def test_bad_usernames(tmp_passwd):
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
            tmp_passwd.create_user(username=bad_username, password="smith")


def test_delete_user(tmp_passwd):
    assert tmp_passwd.has_user(username="john") is False
    tmp_passwd.create_user(username="john", password="smith")
    assert tmp_passwd.has_user(username="john") is True
    tmp_passwd.delete_user(username="john")
    assert tmp_passwd.has_user(username="john") is False


def test_valid_password(tmp_passwd):
    with pytest.raises(ValueError):
        tmp_passwd.valid_password(username="john", password="smith")
    john = tmp_passwd.create_user(username="john", password="smith")
    assert tmp_passwd.valid_password(username="john", password="smith") == john


def test_change_password(tmp_passwd):
    tmp_passwd.create_user(username="john", password="smith")
    tmp_passwd.valid_password(username="john", password="smith")

    tmp_passwd.change_password(username="john", password="jones")
    with pytest.raises(ValueError):
        tmp_passwd.valid_password(username="john", password="smith")
    tmp_passwd.valid_password(username="john", password="jones")


def test_get_user(tmp_passwd):
    with pytest.raises(ValueError):
        tmp_passwd.get_user(username="john")

    user = tmp_passwd.create_user(username="john", password="smith")
    user_john = tmp_passwd.get_user(username="john")
    assert UUID(user.id) == UUID(user_john.id)
    john_again = tmp_passwd.get_user(id=user.id)
    assert john_again == user
    assert tmp_passwd.get_user(user.id) == tmp_passwd.get_user("john") == john_again


def test_create_again(tmp_passwd):
    tmp_passwd.create_user(username="john", password="smith")
    user = tmp_passwd.get_user(username="john")
    assert user is not None

    with pytest.raises(ValueError):
        tmp_passwd.create_user(username="john", password="smith")


def test_all_users(tmp_passwd):
    all_users = tmp_passwd.all_users()
    assert all_users == []

    tmp_passwd.create_user(username="john", password="smith")
    tmp_passwd.create_user(username="admin", password="something")
    all_users = tmp_passwd.all_users()

    assert all_users == [
        ("admin", anything(UUID)),
        ("john", anything(UUID)),
    ]


def test_data(tmp_path):
    passwd = Passwd.for_testing(tmp_path / "passwd")
    passwd.create_user(username="john", password="smith")
    passwd.create_user(username="admin", password="something")

    passwd2 = Passwd.for_testing(tmp_path / "passwd")
    all_users = passwd2.all_users()

    assert all_users == [
        ("admin", anything(UUID)),
        ("john", anything(UUID)),
    ]

    assert tmp_path.joinpath("passwd").is_file()
    assert tmp_path.joinpath("passwd").stat().st_mode & 0o777 == 0o600
    lines = tmp_path.joinpath("passwd").read_text().splitlines()
    lines = [line.strip().split(":", 2) for line in lines if line.strip()]
    assert lines[0][0] == "admin"
    assert lines[1][0] == "john"
    assert UUID(lines[0][1]) and UUID(lines[1][1])
    assert lines[0][2] != lines[1][2]
    assert lines[0][2].startswith("$argon2id$") and lines[1][2].startswith("$argon2id$")


async def test_userbase_to_passwd(tmp_path):
    users_path = tmp_path / "users"
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

    Passwd.convert_userbase_to_passwd(tmp_path / "users", tmp_path / "passwd")

    passwd = Passwd.for_testing(tmp_path / "passwd")

    all_users = passwd.all_users()
    assert all_users == [("admin", admin_id), ("john", john_id)]
    passwd.valid_password(username="john", password="smith")
    passwd.valid_password(username="admin", password="something")


def test_id_or_username(tmp_passwd):
    user = tmp_passwd.create_user(username="john", password="smith")

    tmp_passwd.change_password("john", "jones")
    tmp_passwd.change_password(username="john", password="smith")
    tmp_passwd.change_password("john", password="smith")
    tmp_passwd.change_password(user.id, "jones")
    tmp_passwd.change_password(id=user.id, password="smith")
    tmp_passwd.change_password(user.id, password="smith")


def test_no_cache(tmp_path):
    passwd = Passwd.for_testing(tmp_path / "passwd")
    passwd.create_user(username="john", password="smith")
    assert passwd.has_user(username="john") is True
    passwd2 = Passwd.for_testing(tmp_path / "passwd")
    assert passwd2.has_user(username="john") is True
    passwd.create_user(username="henry", password="williams")
    assert passwd.has_user(username="henry") is True
    assert passwd2.has_user(username="henry") is True
