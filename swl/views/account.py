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

from starlette.responses import RedirectResponse

import logging

logger = logging.getLogger(__name__)


async def show_account(request, swl, **kwargs):
    return swl.success().open_modal(
        data=swl.template("swl/account.j2").render(user=request.user.data)
    )


async def change_password(request, swl, userbase, **kwargs):
    async with request.form() as form:
        username = form["username"]
        current_password = form["current_password"]
        new_password = form["new_password"]
        new_password_repeat = form["new_password_repeat"]

        if username != request.user.username and not request.user.admin:
            return swl.fail().message(
                "Unauthorized; only admin-users can change other users passwords"
            )

        if not userbase.valid_password(username=username, password=current_password):
            return swl.fail().message("Password incorrect")

        if new_password != new_password_repeat:
            return swl.fail().message("Passwords do not match")

        if len(new_password) < 8:
            return swl.fail().message(
                "New password should be at least 8 characters long"
            )

        userbase.change_password(username=username, password=new_password)
        return swl.success().reset_form().toast("Password changed")


async def users_show(request, swl, **kwargs):
    return swl.success().open_modal(
        data=swl.template("swl/users.j2").render(user=request.user.data)
    )


async def users_list(request, userbase, swl, **kwargs):
    async with request.form() as form:
        placeholder = form["placeholder"]
        all_users = userbase.all_users()
        return swl.success().hydrate(
            placeholder,
            data=swl.template("swl/users_list.j2").render(
                users=all_users, request=request
            ),
            rehydrate=dict(
                action=swl.register("users_list"),
                context=dict(placeholder=placeholder),
            ),
        )


async def user_create(request, userbase, swl, **kwargs):
    async with request.form() as form:
        username = form.get("username", "").strip()
        password = form.get("password", "")
        admin = form.get("admin", None) is not None

        if len(username) < 3 or " " in username:
            return swl.fail().message(
                "Username invalid; longer than 3 character and no spaces"
            )

        if not request.user.is_authenticated or not request.user.admin:
            return swl.fail().message("Unauthorized; only admin-users can create users")

        if userbase.exists(username):
            return swl.fail().message("Username already in use")

        userbase.create(username=username, password=password, admin=admin)

        return (
            swl.success()
            .reset_form()
            .rehydrate("placeholder-users_list")
            .toast(f"User {username!r} added")
        )


async def user_delete(request, swl, userbase, **kwargs):
    if not request.user.is_authenticated or not request.user.admin:
        return swl.fail().message("Unauthorized; only admin-users can delete users")

    async with request.form() as form:
        username = form.get("username", "").strip()
        if not userbase.exists(username=username):
            return swl.fail().message("No such user")

        user = userbase.get(username=username)
        if request.user.username == user.username:
            return swl.fail().message("Deleting own user not allowed")

        rehydrate_needed = userbase.delete(username=username)

        response = swl.success()
        return (
            response.rehydrate("placeholder-users_list")
            if rehydrate_needed
            else response
        )


async def user_set_admin(request, swl, userbase, **kwargs):
    if not request.user.admin:
        return swl.fail().message(
            "Unauthorized; only admin-users can set admin on users"
        )

    async with request.form() as form:
        username = form.get("username", "").strip()
        admin = form.get("admin") is not None

        user = userbase.get(username=username)
        if request.user.username == user.username:
            return swl.fail().message("Cannot change admin status of own user")

        user.set_admin(admin)
        userbase.put(user)

        return swl.success().rehydrate("placeholder-users_list")


async def login(request, swl, userbase, **kwargs):
    async with request.form() as form:
        username = form.get("username")
        password = form.get("password")

        next_url = form.get("next", "/")

        if (
            username is not None
            and password is not None
            and userbase.valid_password(username, password)
        ):
            request.session["username"] = username
            return swl.success().redirect(next_url)

        return swl.fail().message("Invalid login credentials")


async def logout(request, **kwargs):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


__actions__ = [
    show_account,
    change_password,
    users_show,
    users_list,
    user_create,
    user_delete,
    user_set_admin,
    dict(method=login, authenticated=False),
]
