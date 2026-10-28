# US Live Industry Proxy Contract

## Status

**Live industry proxy catalog is not enabled.** The source review below identifies candidate
instruments only. It does not establish a license to publish their daily prices or derived returns,
licensed historical classification/membership, point-in-time market capitalization, or rights to
redistribute any of those data. Industry Discovery may read the controlled weekly fixture snapshots;
live mode must report `NO_QUALIFIED_REPRESENTATION` until an authorized dated catalog is supplied.

## Candidate-source research (reviewed 2026-10-28)

| Candidate | Issuer-described exposure | Assessment |
|---|---|---|
| XBI | SSGA describes its benchmark as the Biotechnology segment/sub-industry of the S&P Total Market Index | Candidate for Biotechnology only, subject to effective-dated methodology and rights verification |
| KRE | SSGA describes its benchmark as the Regional Banks segment/sub-industry of the S&P Total Market Index | Candidate for Regional Banks only, subject to effective-dated methodology and rights verification |
| XOP | SSGA describes exposure to Integrated Oil & Gas, Oil & Gas Exploration & Production, and Oil & Gas Refining & Marketing | Not a single-industry proxy; reject as a proxy for any one of these industries |

Issuer materials are useful for screening candidates, not an exhaustive taxonomy or a substitute
for an archived index methodology. Product names alone never qualify a fund.

Primary references:

- [SSGA XBI fund and benchmark description](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-biotech-etf-xbi)
- [SSGA KRE fund and benchmark description](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-regional-banking-etf-kre)
- [SSGA XOP fund and benchmark description](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-oil-gas-exploration-production-etf-xop)
- [MSCI GICS information](https://www.msci.com/indexes/index-resources/gics)
- [S&P DJI GICS information](https://www.spglobal.com/spdji/en/landing/topic/gics/)
- [Massive market-data terms](https://massive.com/terms/market_data_terms.pdf)
- [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)
- [SEC data and research](https://www.sec.gov/data-research)

MSCI/S&P identify GICS as a licensed classification product. SSGA factsheets describe selected
products but do not grant rights to republish GICS data or ETF price-derived results. Massive and
Yahoo usage terms are provider-specific; the current application has no evidence of an account
license permitting third-party or hosted display. The SEC provides filings and company facts, not
a ready-made, complete point-in-time industry-membership and daily market-cap feed. Therefore no
live candidates are registered from these public pages alone.

## Qualification and selection

1. A candidate is keyed by market, stable sector node, stable industry node, instrument symbol,
   source ID, and effective dates. Source availability MUST be no later than the observation date.
2. ETF qualification requires an issuer/index source identifying the ETF's tracked index and a
   documented rule that the index exposure corresponds to one industry. Funds covering multiple
   industries, broad sectors, or merely themed companies do not qualify for a single industry.
3. Use exactly one qualified ETF when available. Multiple qualified ETF matches are an ambiguity
   error until an explicit, dated selection is recorded.
4. Otherwise, a STOCK proxy requires a verified effective-dated industry membership source and
   positive market capitalization observed on the requested date. Select the greatest market cap;
   break equal values by ascending symbol. Label the result **single-company proxy** in all views.
5. A candidate also requires explicit market-data display and derived-data rights for the deployment
   context. A provider ID, public endpoint, ETF factsheet, or personal-use API key does not imply
   rights for a hosted/public product.
6. Missing membership, capitalization, historical methodology, source availability, price history,
   or rights yields `NO_QUALIFIED_REPRESENTATION`; do not use current membership/capitalization
   retrospectively and do not silently omit the industry.
7. Live price comparisons require the industry proxy, parent-sector proxy, and SPY to share an
   eligible ending session and adjusted return basis. Live outcomes are daily evidence, never weekly
   rankings or leadership status.

## Required catalog record

Each enabled candidate must include market, sector/industry IDs, symbol, kind (`ETF` or `STOCK`),
source IDs, composition/membership basis, effective start/end, availability date, rights status,
qualification state, and a reason for rejection. STOCK candidates additionally require dated
membership evidence, positive market cap, and market-cap observation date. No catalog is enabled
until the owner records the license evidence and deployment scope.
