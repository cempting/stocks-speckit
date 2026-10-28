import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import streamlit as st

WORKFLOW_PAGES_STATE_KEY = "market_leadership.workflow_pages"


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    key: str
    title: str
    url_path: str
    icon: str
    render: Callable[[], None]
    default: bool = False


def validate_workflows(workflows: Sequence[WorkflowSpec]) -> tuple[WorkflowSpec, ...]:
    ordered = tuple(workflows)
    if not ordered:
        raise ValueError("workflow registry must not be empty")
    if sum(workflow.default for workflow in ordered) != 1:
        raise ValueError("workflow registry must contain exactly one default")
    keys = [workflow.key for workflow in ordered]
    paths = [workflow.url_path for workflow in ordered]
    if len(set(keys)) != len(keys) or len(set(paths)) != len(paths):
        raise ValueError("workflow keys and URL paths must be unique")
    if any(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) is None for key in keys):
        raise ValueError("workflow keys must be stable lowercase slugs")
    if any(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path) is None for path in paths):
        raise ValueError("workflow URL paths must be stable lowercase slugs")
    return ordered


def to_pages(workflows: Sequence[WorkflowSpec]) -> list[st.Page]:
    return [
        st.Page(
            workflow.render,
            title=workflow.title,
            url_path=workflow.url_path,
            icon=workflow.icon,
            default=workflow.default,
        )
        for workflow in validate_workflows(workflows)
    ]


def register_workflow_pages(
    workflows: Sequence[WorkflowSpec],
) -> list[st.Page]:
    ordered = validate_workflows(workflows)
    pages = to_pages(ordered)
    st.session_state[WORKFLOW_PAGES_STATE_KEY] = {
        workflow.key: page for workflow, page in zip(ordered, pages, strict=True)
    }
    return pages


def workflow_page(key: str) -> Any | None:
    pages = st.session_state.get(WORKFLOW_PAGES_STATE_KEY, {})
    return pages.get(key)


def replace_workflow(
    workflows: Sequence[WorkflowSpec],
    key: str,
    replacement: WorkflowSpec,
) -> tuple[WorkflowSpec, ...]:
    ordered = tuple(workflows)
    matches = [index for index, workflow in enumerate(ordered) if workflow.key == key]
    if len(matches) != 1:
        raise ValueError(f"workflow key is not registered: {key}")
    if replacement.key != key:
        raise ValueError("replacement workflow must keep the registered key")
    updated = list(ordered)
    updated[matches[0]] = replacement
    return validate_workflows(updated)
