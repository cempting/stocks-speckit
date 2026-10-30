"""The table API used here, isolated from Streamlit's optional data-library types."""

from typing import Literal, Protocol, cast

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler
from streamlit.delta_generator import DeltaGenerator
from streamlit.elements.lib.column_types import ColumnConfig
from streamlit.typing import DataframeState


class _StreamlitTables(Protocol):
    def dataframe(
        self,
        data: pd.DataFrame | Styler | list[dict[str, str]],
        *,
        hide_index: bool = True,
        width: Literal["stretch"] = "stretch",
        height: int | Literal["auto"] = "auto",
        key: str | None = None,
        column_config: dict[str, ColumnConfig] | None = None,
    ) -> DeltaGenerator: ...


class _SelectableStreamlitTables(Protocol):
    def dataframe(
        self,
        data: pd.DataFrame,
        *,
        hide_index: bool,
        width: Literal["stretch"],
        key: str,
        column_config: dict[str, ColumnConfig],
        on_select: Literal["rerun"],
        selection_mode: Literal["single-row"],
    ) -> DataframeState: ...


def render_dataframe(
    data: pd.DataFrame | Styler | list[dict[str, str]],
    *,
    hide_index: bool = True,
    width: Literal["stretch"] = "stretch",
    height: int | Literal["auto"] = "auto",
    key: str | None = None,
    column_config: dict[str, ColumnConfig] | None = None,
) -> None:
    cast(_StreamlitTables, st).dataframe(
        data,
        hide_index=hide_index,
        width=width,
        height=height,
        key=key,
        column_config=column_config,
    )


def render_selectable_dataframe(
    data: pd.DataFrame,
    *,
    key: str,
    column_config: dict[str, ColumnConfig],
) -> DataframeState:
    return cast(_SelectableStreamlitTables, st).dataframe(
        data,
        hide_index=True,
        width="stretch",
        key=key,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row",
    )
