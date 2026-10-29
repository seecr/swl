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

Nothing SWL-specific happens here; a real application would use its own database.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

__all__ = ["Task", "TaskStore"]


@dataclass
class Task:
    id: str
    title: str
    notes: str = ""
    done: bool = False
    history: list = field(default_factory=list)  # [{"at": "2026-10-28T16:05:00", "what": "Created"}, ...]

    def log(self, what):
        self.history.append({"at": datetime.now().isoformat(timespec="seconds"), "what": what})


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

    def find(self, q="", status="all"):
        """Tasks matching the search text and status ("all", "open" or "done"), open tasks first."""
        q = q.strip().lower()
        result = [
            task
            for task in self._tasks.values()
            if (not q or q in task.title.lower() or q in task.notes.lower())
            and (status == "all" or task.done == (status == "done"))
        ]
        return sorted(result, key=lambda task: task.done)

    def get(self, task_id):
        return self._tasks.get(task_id)

    def add(self, title, notes=""):
        task = Task(id=uuid.uuid4().hex[:8], title=title, notes=notes)
        task.log("Created")
        self._tasks[task.id] = task
        self._save()
        return task

    def update(self, task_id, title, notes):
        task = self._tasks[task_id]
        if (title, notes) != (task.title, task.notes):
            task.title, task.notes = title, notes
            task.log("Edited")
        self._save()
        return task

    def toggle(self, task_id):
        task = self._tasks[task_id]
        task.done = not task.done
        task.log("Marked as done" if task.done else "Marked as open")
        self._save()
        return task

    def delete(self, task_id):
        task = self._tasks.pop(task_id)
        self._save()
        return task

    def counts(self):
        done = sum(1 for task in self._tasks.values() if task.done)
        return {"open": len(self._tasks) - done, "done": done}

    def _save(self):
        if self._path is not None:
            self._path.write_text(json.dumps([asdict(t) for t in self._tasks.values()], indent=2))
