"""运行入口应保留章节参数，并拒绝含糊或越界的脚本选择。"""

from pathlib import Path
import sys

import pytest

from tools import run_chapter


def test_multiple_scripts_require_a_name_and_outside_script_is_rejected():
    with pytest.raises(ValueError, match="指定脚本"):
        run_chapter.resolve_script("1.6")
    with pytest.raises(ValueError, match="本章"):
        run_chapter.resolve_script("1.6", "../../../common.py")


@pytest.mark.parametrize(
    "arguments", [["2.4", "--budget", "0"], ["2.4", "eval_seed.py", "--budget", "0"]]
)
def test_script_arguments_are_forwarded(monkeypatch, arguments):
    observed = {}
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", list(sys.argv))

    def record(path, run_name):
        observed.update(
            path=Path(path), argv=list(sys.argv), name=run_name, cwd=Path.cwd()
        )

    monkeypatch.setattr(run_chapter.runpy, "run_path", record)
    assert run_chapter.main(arguments) == 0
    assert observed["argv"][1:] == ["--budget", "0"]
    assert observed["path"].name == "eval_seed.py"
    assert observed["name"] == "__main__"
    assert observed["cwd"] == observed["path"].parent


def test_working_directory_is_restored_after_failure(monkeypatch):
    original = Path.cwd()
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", list(sys.argv))

    def fail(path, run_name):
        raise RuntimeError("example failure")

    monkeypatch.setattr(run_chapter.runpy, "run_path", fail)
    with pytest.raises(RuntimeError, match="example failure"):
        run_chapter.main(["2.4"])
    assert Path.cwd() == original
