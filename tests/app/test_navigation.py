from collections.abc import Callable

import pytest

from market_leadership.ui.navigation import (
    WorkflowSpec,
    replace_workflow,
    to_pages,
    validate_workflows,
)


def render_page() -> None:
    return None


def spec(
    key: str,
    url_path: str,
    *,
    default: bool = False,
    render: Callable[[], None] = render_page,
) -> WorkflowSpec:
    return WorkflowSpec(key, key.title(), url_path, ":material/query_stats:", render, default)


def test_registry_requires_exactly_one_default_and_unique_stable_keys_and_paths() -> None:
    workflows = (spec("scoreboard", "scoreboard", default=True), spec("discovery", "discovery"))

    assert validate_workflows(workflows) == workflows
    with pytest.raises(ValueError, match="exactly one default"):
        validate_workflows((spec("a", "a"), spec("b", "b")))
    with pytest.raises(ValueError, match="unique"):
        validate_workflows((spec("same", "a", default=True), spec("same", "b")))
    with pytest.raises(ValueError, match="unique"):
        validate_workflows((spec("a", "same", default=True), spec("b", "same")))


def test_page_conversion_and_workflow_replacement_preserve_registry_order(monkeypatch) -> None:
    workflows = (spec("scoreboard", "scoreboard", default=True), spec("discovery", "discovery"))
    page_arguments: list[dict[str, object]] = []

    def page_factory(render, **kwargs):
        page_arguments.append({"render": render, **kwargs})
        return kwargs["url_path"]

    monkeypatch.setattr("market_leadership.ui.navigation.st.Page", page_factory)

    pages = to_pages(workflows)

    assert pages == ["scoreboard", "discovery"]
    assert [arguments["title"] for arguments in page_arguments] == [
        "Scoreboard",
        "Discovery",
    ]
    assert page_arguments[0]["default"] is True
    assert page_arguments[1]["default"] is False


@pytest.mark.parametrize("key", ["scoreboard", "discovery"])
def test_any_workflow_can_be_replaced_without_changing_registry_order(key: str) -> None:
    workflows = (spec("scoreboard", "scoreboard", default=True), spec("discovery", "discovery"))
    current = next(workflow for workflow in workflows if workflow.key == key)
    replacement = spec(
        key,
        current.url_path,
        default=current.default,
        render=lambda: None,
    )

    updated = replace_workflow(workflows, key, replacement)

    assert [workflow.key for workflow in updated] == ["scoreboard", "discovery"]
    assert updated[workflows.index(current)] is replacement
