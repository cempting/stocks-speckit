"""Session-local appearance without changing server-wide Streamlit configuration."""

import streamlit as st


def toggle_dark_mode() -> None:
    st.session_state["dark_mode"] = not bool(st.session_state.get("dark_mode", False))


def apply_theme() -> None:
    dark = bool(st.session_state.get("dark_mode", False))
    background = "#111820" if dark else "#f7f8f6"
    surface = "#18232d" if dark else "#e9eeea"
    foreground = "#edf3f7" if dark else "#17212b"
    muted = "#aebbc8" if dark else "#64707d"
    border = "#3b4c5b" if dark else "#cbd3cf"
    st.html(
        f"""
        <style>
        .st-key-theme_action button [data-testid="stMarkdownContainer"] {{
            position: absolute;
            width: 1px;
            height: 1px;
            overflow: hidden;
            clip-path: inset(50%);
            white-space: nowrap;
        }}
        .stApp {{
            --app-background: {background};
            --app-surface: {surface};
            --app-foreground: {foreground};
            --app-muted: {muted};
            --app-border: {border};
            background: var(--app-background);
            color: var(--app-foreground);
            color-scheme: {"dark" if dark else "light"};
        }}
        .stApp [data-testid="stHeader"],
        .stApp [data-testid="stBottom"] {{
            background: var(--app-background);
        }}
        .stApp [data-testid="stSidebar"] {{
            background: var(--app-surface);
        }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp [data-testid="stWidgetLabel"],
        .stApp [data-testid="stMarkdownContainer"],
        .stApp [data-baseweb="tab"] {{
            color: var(--app-foreground);
        }}
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stCaptionContainer"] p {{
            color: var(--app-muted);
        }}
        .stApp [data-testid="stDateInput"] > div,
        .stApp [data-testid="stSelectbox"] [role="group"],
        .stApp [data-testid="stMultiSelect"] [role="group"],
        .stApp input[role="combobox"],
        .stApp [data-testid="stTextInput"] input,
        .stApp [data-testid="stNumberInput"] input {{
            background: var(--app-surface);
            color: var(--app-foreground);
            border-color: var(--app-border);
        }}
        .stApp input::placeholder,
        .stApp [data-testid="stDateInput"] [data-type],
        .stApp [data-testid="stDateInput"] button,
        .stApp [data-testid="stSelectbox"] button,
        .stApp [data-testid="stMultiSelect"] button {{
            color: var(--app-muted);
        }}
        .stApp [data-baseweb="input"],
        .stApp [data-baseweb="input"] input,
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="textarea"],
        .stApp [data-baseweb="textarea"] textarea {{
            background: var(--app-surface);
            color: var(--app-foreground);
            border-color: var(--app-border);
        }}
        .stApp [data-baseweb="select"] svg {{
            fill: var(--app-foreground);
        }}
        .stApp button[kind="secondary"],
        .stApp button[kind="tertiary"],
        .stApp button[kind="segmented_control"],
        .stApp button[data-variant="secondary"],
        .stApp button[data-variant="tertiary"],
        .stApp button[data-variant="segmented_control"] {{
            background: var(--app-background);
            color: var(--app-foreground);
            border-color: var(--app-border);
        }}
        .stApp button[role="radio"][aria-checked="true"],
        .stApp button[kind="segmented_controlActive"] {{
            background: var(--app-surface);
            border-color: #c4493d;
        }}
        .stApp button[kind="secondary"]:hover,
        .stApp button[kind="tertiary"]:hover {{
            background: var(--app-surface);
            border-color: #c4493d;
        }}
        .stApp [data-baseweb="popover"],
        .stApp [data-baseweb="popover"] [role="listbox"],
        .stApp [data-baseweb="popover"] [role="option"],
        .stApp [data-baseweb="calendar"],
        .stApp [data-testid="stTooltipContent"] {{
            background: var(--app-surface);
            color: var(--app-foreground);
        }}
        .stApp [data-baseweb="popover"] [role="option"]:hover {{
            background: var(--app-background);
        }}
        </style>
        """
    )
