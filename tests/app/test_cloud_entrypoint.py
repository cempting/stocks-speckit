from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.bootstrap import build_workflow_registry


def test_cloud_entrypoint_defaults_to_weekly_and_keeps_discovery_available(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    app_path = Path(__file__).parents[2] / "streamlit_app.py"

    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Weekly Sector Leadership"
    registry = build_workflow_registry(lambda: None, lambda: None)
    assert [(workflow.key, workflow.default) for workflow in registry] == [
        ("weekly-scoreboard", True),
        ("sector-discovery", False),
    ]
