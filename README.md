# stocks-speckit
SDD + Python = Awesome App for Stock Screening

## Local configuration

Copy the tracked environment template and add credentials only to the ignored local file:

```bash
cp .env.example .env
```

Set `MASSIVE_API_KEY` in `.env` to enable the Massive REST provider. `yfinance` does not require an
API key. Live provider responses are persisted under `.cache/market-data` by default; set
`MARKET_DATA_CACHE_PATH` to use another local directory. Never commit `.env`.

## Run locally

```bash
uv sync
uv run streamlit run streamlit_app.py
```

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io), create an app from the repository.
3. Set the entrypoint to `streamlit_app.py` and the Python version to `3.12`.
4. Deploy. Community Cloud detects `uv.lock` and installs the project and its dependencies with
	`uv`.

The default `yfinance` provider needs no secret. To enable and select Massive, add these root-level
values in the portal's **Advanced settings > Secrets** field:

```toml
MASSIVE_API_KEY = "your-key"
MARKET_DATA_PROVIDER = "massive"
```

Do not commit `.streamlit/secrets.toml` or any provider credential.