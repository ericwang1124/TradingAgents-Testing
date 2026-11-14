"""Headline parsing for earnings, guidance and analyst signals (no network)."""

import pandas as pd

from tradingagents.strategies.vcp import news


def test_parse_reports_against_estimates_and_year_over_year():
    assert news.parse("Super Micro Computer Q1 EPS $3.43 Beats $3.20 Estimate, Sales $2.12B Beat $2.06B Estimate") == {"eps": 1.0, "sales": 1.0}
    assert news.parse("XYZ Q3 Adj. EPS $(0.12) Misses $(0.10) Estimate, Sales $50.1M Beat $49M Estimate") == {"eps": -1.0, "sales": 1.0}
    assert news.parse("ABC Q2 EPS $1.05 vs $0.98 Est., Sales $1.21B vs $1.25B Est.") == {"eps": 1.0, "sales": -1.0}
    old = news.parse("Boot Barn Reports Q1 EPS $0.03 vs $0.02 In Same Qtr. Last Year, Sales $139.4M vs $133.4M YoY, Comps Up 4.5%")
    assert old == {"eps": 1.0, "sales": 0.0}                              # sales up 4.5%: growing, but under the 10% bar
    assert news.parse("Fast Co Reports Q4 EPS $0.40 vs $0.10 In Same Qtr. Last Year, Sales $300M vs $200M YoY") == {"eps": 1.0, "sales": 1.0}


def test_parse_guidance_and_analysts():
    assert news.parse("e.l.f Beauty Raises FY23 Adj. EPS Guidance From $0.84-$0.87 To $1.07-$1.10 vs $0.91 Est., Raises Sales Guidance From "
                      "$448M-$456M To $478M-$486M vs $459.45M Est.") == {"guidance": 1.0}
    assert news.parse("Supermicro Provides Q2 Fiscal 2024 Business Update; Updates Q2 EPS Guidance From $4.40-$4.88 To $5.40-$5.55 "
                      "Vs $4.52 Est.; Net Sales From $2.7B-$2.9B To $3.6B-$3.65B") == {"guidance": 1.0}
    assert news.parse("Weak Corp Cuts FY24 Sales Outlook") == {"guidance": -1.0}
    assert news.parse("Acme Sees Q3 Sales $1.10B-$1.20B vs $1.05B Est") == {"guidance": 1.0}
    assert news.parse("Boot Barn Sees FY18 EPS $0.52-$0.57, Flat To Positive Comps") == {}
    assert news.parse("JP Morgan Maintains Overweight on e.l.f. Beauty, Raises Price Target to $48") == {"analyst": 1.0}
    assert news.parse("UBS Maintains Neutral on Twitter, Lowers Price Target to $62") == {"analyst": -1.0}
    assert news.parse("Goldman Sachs Upgrades Acme to Buy") == {"analyst": 1.0}
    assert news.parse("Benzinga Opening Bell Update: Apple Gains On Earnings And Buyback") == {}


def test_signals_use_only_what_was_published_before_the_cutoff():
    items = [("2024-01-19T13:37:00Z", "Supermicro Updates Q2 EPS Guidance From $4.40-$4.88 To $5.40-$5.55 Vs $4.52 Est."),
             ("2024-01-19T13:18:00Z", "Barclays Maintains Overweight on Super Micro Computer, Raises Price Target to $396"),
             ("2023-11-01T20:13:00Z", "Super Micro Computer Q1 EPS $3.43 Beats $3.20 Estimate, Sales $2.12B Beat $2.06B Estimate"),
             ("2023-05-02T20:13:00Z", "Super Micro Computer Q3 EPS $1.63 Misses $1.70 Estimate, Sales $1.28B Miss $1.40B Estimate")]
    before = news.signals(items, pd.Timestamp("2024-01-18 19:00"))
    assert before["eps"] == 1.0 and before["sales"] == 1.0 and before["guidance"] == 0.0 and before["analyst"] == 0.0
    after = news.signals(items, pd.Timestamp("2024-01-19 19:00"))
    assert after["guidance"] == 1.0 and after["analyst"] == 1.0 and after["report"] == 78.0
    stale = news.signals(items, pd.Timestamp("2023-10-15 19:00"))            # the May report is more than 95 days old
    assert stale["eps"] != stale["eps"]
