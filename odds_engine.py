"""
Odds Engine
-----------
When bets come in, odds shift to reflect the market.
We use a simple implied-probability model:
  - Calculate the proportion of money on each side
  - Convert back to decimal odds with a small house margin (vig)
  - Clamp odds so they never go below 1.05 (guaranteed payout) or above 20.0
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
import models

VIG = 0.05          # 5% house edge baked into odds
MIN_ODDS = 1.05
MAX_ODDS = 20.0
BASE_POOL = 100.0   # virtual seed liquidity so first bet doesn't spike odds wildly


def recalculate_odds(db: Session, matchup_id: int):
    """Return (odds_a, odds_b) after accounting for all bets on this matchup."""

    # Sum of money bet on each side
    result = (
        db.query(
            models.Bet.pick,
            func.sum(models.Bet.amount).label("total"),
        )
        .filter(models.Bet.matchup_id == matchup_id)
        .group_by(models.Bet.pick)
        .all()
    )

    totals = {"A": BASE_POOL, "B": BASE_POOL}
    for row in result:
        totals[row.pick] = BASE_POOL + (row.total or 0)

    pool = totals["A"] + totals["B"]

    # Implied probabilities
    prob_a = totals["A"] / pool
    prob_b = totals["B"] / pool

    # Apply vig: inflate probabilities so they sum to > 1
    prob_a_vig = prob_a * (1 + VIG)
    prob_b_vig = prob_b * (1 + VIG)

    # Convert to decimal odds (1 / implied_prob), clamped
    odds_a = max(MIN_ODDS, min(MAX_ODDS, 1 / prob_a_vig))
    odds_b = max(MIN_ODDS, min(MAX_ODDS, 1 / prob_b_vig))

    return round(odds_a, 2), round(odds_b, 2)
