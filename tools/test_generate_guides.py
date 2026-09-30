"""生成教程需提供可运行的新命令，且不能改写现有文件进行自检。"""

from pathlib import Path

import pytest

from tools import generate_project_guides as guides


@pytest.mark.parametrize(
    "step",
    [
        "m2-session-langgraph/step1",
        "m5-injection-pii-observability/step1",
        "m8-evidence-final-frontend/step2",
    ],
)
def test_generated_commands_reference_current_layout(monkeypatch, step):
    outputs = {}

    def capture(path, text, **kwargs):
        outputs[path] = text
        return len(text)

    monkeypatch.setattr(Path, "write_text", capture)
    folder = guides.ROOT / "flagship-project" / step
    original = (
        (folder / "README.md")
        .read_text(encoding="utf-8")
        .split(guides.REFERENCE_HEADING, 1)[0]
        .rstrip()
    )
    guides.render(step)
    assert set(outputs) == {folder / "README.md"}
    for path, text in outputs.items():
        assert path.parent == folder
        assert "materialize.py flagship" in text
        assert "materialize_day.py" not in text
        assert "day_change_report.py" not in text
        assert "D:\\workspace" not in text
    readme = outputs[folder / "README.md"]
    assert readme.startswith(original)
    assert readme.count(guides.REFERENCE_HEADING) == 1
    assert "& $python -m pytest" in readme
    assert "cd .build/flagship/" in readme
