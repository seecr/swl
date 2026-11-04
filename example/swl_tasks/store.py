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

"""
Storage for the example: tasks kept in memory and saved to a JSON file.

Nothing SWL-specific happens here (apart from marking texts for translation with N_);
a real application would use its own database.

A task is shared (everyone sees it) or private: only its owner sees it.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

from swl.i18n import N_

__all__ = ["Task", "TaskStore"]


@dataclass
class Task:
    id: str
    title: str
    notes: str = ""
    done: bool = False
    owner: str = ""  # username of who made it
    private: bool = False  # only the owner sees it
    # [{"at": "2026-10-28T16:05:00", "what": "Created"}, ...]; "what" is English, shown
    # translated (tab_history.j2)
    history: list = field(default_factory=list)

    def visible_to(self, username):
        return not self.private or self.owner == username

    def log(self, what):
        self.history.append(
            {"at": datetime.now().isoformat(timespec="seconds"), "what": what}
        )


class TaskStore:
    # Identifies "the list of tasks" in change notifications over the websocket
    # (see Dispatcher.signal_change and data-swl-on-changed in page.j2).
    qid = "tasks"

    def __init__(self, path=None):
        self._path = path
        self._tasks = {}
        if path is not None and path.is_file():
            for data in json.loads(path.read_text()):
                task = Task(**data)
                self._tasks[task.id] = task

    def find(self, username, q="", status="all"):
        """The tasks this user may see, matching the search text and status ("all",
        "open" or "done"), open tasks first."""
        q = q.strip().lower()
        result = [
            task
            for task in self._tasks.values()
            if task.visible_to(username)
            and (not q or q in task.title.lower() or q in task.notes.lower())
            and (status == "all" or task.done == (status == "done"))
        ]
        return sorted(result, key=lambda task: task.done)

    def get(self, task_id, username):
        """The task, if this user may see it."""
        task = self._tasks.get(task_id)
        return task if task is not None and task.visible_to(username) else None

    def add(self, title, owner, notes="", private=False):
        task = Task(
            id=uuid.uuid4().hex[:8],
            title=title,
            notes=notes,
            owner=owner,
            private=private,
        )
        task.log(N_("Created"))
        self._tasks[task.id] = task
        self._save()
        return task

    def update(self, task_id, title, notes, private):
        task = self._tasks[task_id]
        if (title, notes) != (task.title, task.notes):
            task.title, task.notes = title, notes
            task.log(N_("Edited"))
        if private != task.private:
            task.private = private
            task.log(N_("Made private") if private else N_("Shared"))
        self._save()
        return task

    def toggle(self, task_id):
        task = self._tasks[task_id]
        task.done = not task.done
        task.log(N_("Marked as done") if task.done else N_("Marked as open"))
        self._save()
        return task

    def move(self, task_id, username, done, position, q=""):
        """Move a task to open or done (done), at position among the tasks this user sees
        there with search text q (as in the tree: views.task_tree_move). The order is kept
        in the order of the tasks."""
        task = self._tasks[task_id]
        if task.done != done:
            task.done = done
            task.log(N_("Marked as done") if done else N_("Marked as open"))
        siblings = [
            t
            for t in self.find(username, q=q, status="done" if done else "open")
            if t.id != task_id
        ]
        order = [t for t in self._tasks.values() if t.id != task_id]
        if position < len(siblings):
            index = order.index(siblings[max(position, 0)])  # just before that one
        elif siblings:
            index = order.index(siblings[-1]) + 1  # after the last one
        else:
            index = len(order)
        order.insert(index, task)
        self._tasks = {t.id: t for t in order}
        self._save()
        return task

    def delete(self, task_id):
        task = self._tasks.pop(task_id)
        self._save()
        return task

    def counts(self, username):
        tasks = [task for task in self._tasks.values() if task.visible_to(username)]
        done = sum(1 for task in tasks if task.done)
        return {"open": len(tasks) - done, "done": done}

    def _save(self):
        if self._path is not None:
            self._path.write_text(
                json.dumps([asdict(t) for t in self._tasks.values()], indent=2)
            )
