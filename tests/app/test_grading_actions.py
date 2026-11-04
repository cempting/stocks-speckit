from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.support.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]


def test_root_does_not_render_legacy_fundamental_grading_actions(monkeypatch) -> None:
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Discovery", "Industry Deep-Dive"]
    assert not any(
        button.label in {"Load fundamentals", "Refresh displayed stocks"} for button in app.button
    )
    screening_prefix = "market_leadership.screening."
    assert not any(
        widget.key and widget.key.startswith(screening_prefix)
        for widget in (*app.selectbox, *app.multiselect)
    )
