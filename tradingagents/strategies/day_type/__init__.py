"""Day-type regimes decided at 10:00 ET from the pre-market (09:00-09:30) and the first 30 minutes.

At 10:00 each session is either traded for *continuation* (with the 09:30-10:00 move), for
*reversal* (against it), or not at all, holding to 12:00 or to the close. The mapping from the
10:00 features to that choice is a fixed Dalton-style rule or is learned walk-forward from
earlier years only.
"""
