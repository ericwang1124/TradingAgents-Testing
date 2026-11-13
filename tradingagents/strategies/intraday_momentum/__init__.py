"""Published SPY intraday momentum rules, re-tested on our own minute data with their stated
parameters (no tuning):

* ``half_hour`` — Gao, Han, Li & Zhou (2018, JFE) "Market intraday momentum": the sign of the
  return from the prior close to 10:00 sets the position for the last half hour (15:30-16:00).
* ``noise_area`` — Zarattini, Aziz & Barbon (2024, SSRN) "Beat the Market: An Effective Intraday
  Momentum Strategy for S&P500 ETF (SPY)": trade breakouts of a time-of-day "noise area" built
  from the average absolute move from the open over the last 14 sessions, checked every 30
  minutes, trailing stop at max/min(boundary, VWAP), flat at the close, volatility-targeted size.
"""
