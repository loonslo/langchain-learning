"""验证累积项目还原的隔离、覆盖、删除和失败边界。"""

import pytest

from tools import materialize as module


@pytest.fixture
def track(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BUILD_ROOT", tmp_path / ".build")
    sequence = [
        "flagship-project/m1/step1",
        "flagship-project/m1/step2",
        "flagship-project/m2/step1",
    ]
    monkeypatch.setitem(
        module.TRACKS, "flagship", {"sequence": sequence, "target_name": "app"}
    )
    for step in sequence:
        (tmp_path / step).mkdir(parents=True)
    return tmp_path, [tmp_path / step for step in sequence]


def test_overlay_delete_directory_and_exclude_lesson_files(track):
    root, steps = track
    (steps[0] / "src").mkdir()
    (steps[0] / "src/a.py").write_text("old")
    (steps[0] / "keep.py").write_text("v1")
    (steps[0] / "README.md").write_text("lesson")
    (steps[0] / ".env").write_text("LOCAL_CONFIG=fixture")
    (steps[1] / "keep.py").write_text("v2")
    (steps[1] / "deleted_files.txt").write_text("src\n")
    assert module.snapshot("flagship", 1) == {"keep.py": b"v2"}
    target = module.materialize("flagship", "m1/step2")
    assert target == root / ".build/flagship/m1/step2/app"
    assert (target / "keep.py").read_text() == "v2"


def test_repeated_step_names_are_isolated_and_ambiguous_target_is_rejected(track):
    first = module.materialize("flagship", "m1/step1")
    marker = first / "local.txt"
    marker.write_text("preserve")
    second = module.materialize("flagship", "m2/step1")
    assert first != second
    assert marker.read_text() == "preserve"
    with pytest.raises(ValueError, match="歧义"):
        module.resolve_index("flagship", "step1")


def test_missing_input_does_not_destroy_existing_build(track):
    _, steps = track
    target = module.materialize("flagship", "m1/step1")
    (target / "local.txt").write_text("preserve")
    steps[0].rmdir()
    with pytest.raises(FileNotFoundError):
        module.materialize("flagship", "m1/step1")
    assert (target / "local.txt").read_text() == "preserve"


def test_manifest_cannot_escape_project_and_negative_index_is_rejected(track):
    _, steps = track
    (steps[1] / "deleted_files.txt").write_text("../outside.txt\n")
    with pytest.raises(ValueError, match="非法删除"):
        module.snapshot("flagship", 1)
    with pytest.raises(ValueError, match="索引"):
        module.snapshot("flagship", -1)
