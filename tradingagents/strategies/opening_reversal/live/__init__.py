"""Live (paper) operation of the opening reversal short, gated by a daily pre-market decision.

Daily flow (see README "实盘模拟" section):
  1. ``briefing``  — pre-market snapshot: gap, regime, VIX, scheduled events, news, hard rules
  2. ``decide``    — record the GO / NO_GO decision (made by the Claude session) with reasons
  3. ``run``       — watch 09:35-10:30 for the signal; on GO buy a 0DTE SPY put on Alpaca *paper*
  4. ``evaluate``  — afterwards, fill in shadow R (traded or not) and the paper option P&L
"""
