from .utils import Views

from contextlib import contextmanager
import sys
import types


@contextmanager
def append_to_syspath(path):
    orig_path = sys.path[:]
    sys.path.append(path)
    try:
        yield
    finally:
        sys.path = orig_path


def test_Views(tmp_path):
    views_dir = tmp_path / "views"
    views_dir.mkdir(parents=True, exist_ok=True)

    (views_dir / "__init__.py").write_text("")
    (views_dir / "a_view.py").write_text("")
    (views_dir / "b_view.py").write_text("")

    with append_to_syspath(tmp_path.as_posix()):
        views = Views(views_dir.stem, ["a_view"])
        assert isinstance(views.a_view, types.ModuleType)
        assert len(views.modules) == 1
        assert list(views.modules)[0] is views.a_view

    with append_to_syspath(tmp_path.as_posix()):
        views = Views(views_dir.stem, ["a_view", "b_view"])
        assert isinstance(views.a_view, types.ModuleType)
        assert isinstance(views.b_view, types.ModuleType)
        assert len(views.modules) == 2
