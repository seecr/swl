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

import json
import secrets
import uuid
import warnings
from pathlib import Path

import argon2
import argon2.profiles
from starlette.authentication import BaseUser
from collections import namedtuple
import functools

import re

ADMIN_USERNAME = "admin"

valid_username_re = re.compile(r"^[a-z0-9_-]+$")


def sanitized(username):
    result = username.lower().strip()
    if not valid_username_re.match(result):
        raise ValueError(f"Invalid username: {username!r}")
    return result


def uuid_gen():
    return str(uuid.uuid1())


def id_or_username(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if len(args) > 0:
            id_or_username, remainder = args[0], args[1:]
            args = (sanitized(id_or_username),) + remainder
        else:
            id_or_username = kwargs.pop("id", None) or kwargs.pop("username", None)
            kwargs["id_or_username"] = sanitized(id_or_username)
        return fn(self, *args, **kwargs)

    return wrapper


User = namedtuple("User", ["username", "id"])
_UserLine = namedtuple("UserLine", ["username", "id", "hash"])


class Passwd:
    def __init__(self, path, _hasher=None):
        self._hasher = _hasher or argon2.PasswordHasher()
        self._path = Path(path)
        if self._path.is_dir():
            raise ValueError(f"Path {self._path} is a directory, expected a file")
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def for_testing(cls, path):
        return cls(
            path,
            _hasher=argon2.PasswordHasher.from_parameters(argon2.profiles.CHEAPEST),
        )

    def create_user(self, username, password):
        username = sanitized(username)
        users = self._list_userlines()
        if username in {l.username for l in users}:
            raise ValueError(f"User {username} already exists")
        user_id = uuid_gen()
        password_hash = self._hasher.hash(password)
        userline = _UserLine(username=username, id=user_id, hash=password_hash)
        self._save(userline)
        return User(username=username, id=user_id)

    @id_or_username
    def has_user(self, id_or_username):
        userlines = self._list_userlines()
        ids_and_usernames = {l.id for l in userlines} | {l.username for l in userlines}
        return id_or_username in ids_and_usernames

    @id_or_username
    def get_user(self, id_or_username):
        userline = self._find_userline(id_or_username)
        if userline is None:
            raise ValueError(f"User {id_or_username} does not exist")
        return User(username=userline.username, id=userline.id)

    @id_or_username
    def delete_user(self, id_or_username):
        userline = self._find_userline(id_or_username)
        if userline is not None:
            self._remove(userline)

    def valid_password(self, username, password):
        username = sanitized(username)
        userline = self._find_userline(username)
        try:
            if userline is not None and self._hasher.verify(userline.hash, password):
                return User(username=userline.username, id=userline.id)
        except argon2.exceptions.VerifyMismatchError:
            pass
        raise ValueError(f"User or password invalid")

    @id_or_username
    def change_password(self, id_or_username, password):
        userline = self._find_userline(id_or_username)
        if userline is None:
            raise ValueError(f"User {id_or_username} does not exist")
        password_hash = self._hasher.hash(password)
        new_userline = _UserLine(
            username=userline.username, id=userline.id, hash=password_hash
        )
        self._save(new_userline)

    def all_users(self):
        return [
            User(username=user.username, id=user.id)
            for user in sorted(self._list_userlines())
        ]

    def _save(self, userline):
        self._save_data(
            self._path,
            [l for l in self._list_userlines() if l.id != userline.id] + [userline],
        )

    def _remove(self, userline):
        self._save_data(
            self._path, [l for l in self._list_userlines() if l.id != userline.id]
        )

    @classmethod
    def _save_data(cls, path, userlines):
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w") as f:
            for user in sorted(userlines):
                f.write(f"{user.username}:{user.id}:{user.hash}\n")
        tmp_path.replace(path)
        path.chmod(0o600)

    def _list_userlines(self):
        if not self._path.is_file():
            return []
        data = self._path.read_text()
        return [
            _UserLine(*l.split(":", 2))
            for l in data.splitlines()
            if l.count(":") == 2 and not l.startswith("#")
        ]

    def _find_userline(self, id_or_username):
        for line in self._list_userlines():
            if line.id == id_or_username or line.username == id_or_username:
                return line
        return None

    @classmethod
    def convert_userbase_to_passwd(cls, userbase_path, passwd_path):
        if Path(passwd_path).exists():
            raise ValueError(f"Passwd file {passwd_path} already exists")
        userlines = []
        for userfile in Path(userbase_path).glob("*.json"):
            userinfo = json.loads(userfile.read_text())
            userlines.append(
                _UserLine(
                    username=userinfo["username"],
                    id=userinfo["id"],
                    hash=userinfo["password"],
                )
            )
        if not userlines:
            raise ValueError(f"No users found in userbase {userbase_path}")
        cls._save_data(passwd_path, userlines)
