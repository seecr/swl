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

import json
import secrets
import uuid
import warnings
from pathlib import Path

import argon2
import argon2.profiles
from starlette.authentication import BaseUser
from .passwd import Passwd

import re

ADMIN_USERNAME = "admin"

valid_username_re = re.compile(r"^[a-z0-9_-]+$")


def sanitized(username):
    result = username.lower().strip()
    if not valid_username_re.match(result):
        raise ValueError(f"Invalid username: {username!r}")
    return result


class Userbase:
    def __init__(self, path, user_class=None, _hasher=None):
        self._user_class = user_class or UserbaseUser
        self._path = Path(path)
        if self._path.joinpath("users").is_dir():
            warnings.warn(
                DeprecationWarning(
                    "Userbase path should not be the parent of the 'users' directory, but the 'users' directory itself."
                )
            )
            self._path = self._path.joinpath("users")
        self._path.mkdir(parents=True, exist_ok=True)
        if (
            not self._path.joinpath("passwd").is_file()
            and len(list(self._path.glob("*.json"))) > 0
        ):
            warnings.warn(
                DeprecationWarning("Userbase will be converted to use a passwd file.")
            )
            self.convert_to_passwd(self._path, _hasher, self._user_class)
        self._passwd = Passwd(self._path / "passwd", _hasher=_hasher)

    def ensure_admin(self, file_path=None):
        admin_users = [user for user in self.all_users() if user["admin"]]
        if not admin_users:
            admin_password = secrets.token_urlsafe(12)
            self.create(
                username=ADMIN_USERNAME, password=admin_password, admin=True, force=True
            )

            if file_path is None:
                print(f"Admin password: {admin_password}", flush=True)
            else:
                file_path.write_text(
                    f"Admin user created; initial password: {admin_password}"
                )
            return admin_password

    def exists(self, username):
        return self._passwd.has_user(username=username)

    def create(self, username, password, admin=False, force=False):
        if self._passwd.has_user(username) and not force:
            raise ValueError(f"User {username!r} already exists")
        pwduser = self._passwd.create_user(username=username, password=password)
        user = self._user_class(
            dict(
                username=pwduser.username,
                admin=admin,
                id=pwduser.id,
            )
        )
        self._store_user(pwduser, user)
        return user

    def delete(self, username):
        try:
            pwduser = self._passwd.get_user(username=username)
        except ValueError:
            return False
        user = self._load_user(pwduser)
        if user.admin:
            return False
        (self._path / f"{user.id}.json").unlink()
        self._passwd.delete_user(pwduser.id)
        return True

    def get(self, username):
        try:
            pwduser = self._passwd.get_user(username=username)
        except ValueError:
            return None
        return self._load_user(pwduser)

    def put(self, user):
        pwduser = self._passwd.get_user(user.id)
        self._store_user(pwduser, user)

    def valid_password(self, username, password):
        try:
            self._passwd.valid_password(username=username, password=password)
            return True
        except ValueError:
            return False

    def change_password(self, username, password):
        return self._passwd.change_password(username=username, password=password)

    def all_users(self):
        pwd_users = self._passwd.all_users()
        result = []
        for pwduser in pwd_users:
            user = self._load_user(pwduser)
            result.append(
                dict(username=user["username"], admin=user.get("admin", False))
            )
        return sorted(result, key=lambda user: user["username"])

    def _load_user(self, pwduser):
        if (userfile := self._path / f"{pwduser.id}.json").is_file() is False:
            return None
        return self._user_class(
            json.loads(userfile.read_text(), object_hook=self._user_class.decoder)
            | {"id": pwduser.id, "username": pwduser.username}
        )

    def _store_user(self, pwduser, user):
        userfile = self._path / f"{pwduser.id}.json"
        userdata = {k: v for k, v in user.data.items() if k not in ("id", "username")}
        userfile_tmp = userfile.with_suffix(".tmp")
        userfile_tmp.write_text(
            json.dumps(userdata, indent=2, cls=self._user_class.encoder())
        )
        userfile_tmp.rename(userfile)

    @classmethod
    def convert_to_passwd(cls, users_path, hasher, user_class):
        passwd_path = users_path / "passwd"
        Passwd.convert_userbase_to_passwd(users_path, passwd_path)
        pwd = Passwd(passwd_path, _hasher=hasher)
        for user in pwd.all_users():
            old_userfile = users_path / f"{user.username}.json"
            userfile = users_path / f"{user.id}.json"
            old_data = json.loads(old_userfile.read_text())
            userfile.write_text(
                json.dumps(
                    {
                        k: v
                        for k, v in old_data.items()
                        if k not in ("id", "username", "password")
                    },
                    indent=2,
                    cls=user_class.encoder(),
                )
            )
            old_userfile.unlink()

    @classmethod
    def for_testing(cls, path):
        return cls(
            path,
            _hasher=argon2.PasswordHasher.from_parameters(argon2.profiles.CHEAPEST),
        )


class UserbaseUser(BaseUser):
    def __init__(self, user):
        self._user = user

    @property
    def display_name(self):
        return self._user["username"]

    @property
    def id(self):
        return self._user["id"]

    @classmethod
    def encoder(cls):
        return json.JSONEncoder

    @classmethod
    def decoder(cls, dct):
        return dct

    @property
    def is_authenticated(self):
        return True

    @property
    def admin(self):
        return self.get("admin", False)

    @property
    def username(self):
        return self._user["username"]

    def set_admin(self, admin=True):
        self._user["admin"] = admin

    def __getitem__(self, *args, **kwargs):
        return self._user.__getitem__(*args, **kwargs)

    def __setitem__(self, *args, **kwargs):
        return self._user.__setitem__(*args, **kwargs)

    def __contains__(self, *args, **kwargs):
        return self._user.__contains__(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._user.get(*args, **kwargs)

    @property
    def data(self):
        return self._user
