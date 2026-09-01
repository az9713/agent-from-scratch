from __future__ import annotations

import ast
from pathlib import Path


def test_tutorial_comments_do_not_change_the_program():
    """Comments vanish from the AST, so the tutorial must match agent.py exactly."""

    root = Path(__file__).resolve().parents[1]
    canonical = ast.parse((root / "agent.py").read_text(encoding="utf-8"))
    tutorial = ast.parse((root / "agent_tutorial.py").read_text(encoding="utf-8"))

    assert ast.dump(tutorial, include_attributes=False) == ast.dump(
        canonical, include_attributes=False
    )
