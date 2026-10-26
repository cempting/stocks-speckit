# stocks-speckit
SDD + Python = Awesome App for Stock Screening

## Local configuration

Copy the tracked environment template and add credentials only to the ignored local file:

```bash
cp .env.example .env
```

Set `MASSIVE_API_KEY` in `.env` to enable the Massive REST provider. `yfinance` does not require an
API key. Never commit `.env`.