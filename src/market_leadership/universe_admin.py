"""Compatibility entry point for explicit legacy maintenance."""

import sys


def main(argv: list[str] | None = None) -> int:
    try:
        from market_data_tools.legacy.universe_admin import main as maintain
    except ModuleNotFoundError as error:
        if error.name != "market_data_tools":
            raise
        print(
            "Install market-leadership[maintenance] for explicit legacy administration.",
            file=sys.stderr,
        )
        return 2
    return maintain(argv)


if __name__ == "__main__":
    raise SystemExit(main())
