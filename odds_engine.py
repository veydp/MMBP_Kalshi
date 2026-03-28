"""
Odds Engine
-----------
When bets come in, odds shift to reflect the market.
Base pool is seeded from the matchup's starting odds so that
when all bets are removed, odds return to the original seed-based values.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
import models

VIG = 0.05
MIN_ODDS = 1.05
MAX_ODDS = 20.0
BASE_POOL = 200.0   # total virtual liquidity split proportionally by starting odds


def recalculate_odds(db: Session, matchup_id: int):
    """Return (odds_a, odds_b) after accounting for all bets on this matchup."""

    matchup = db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()
    if not matchup:
        return 2.0, 2.0

    # Use INITIAL odds (never changes) to set the base pool proportions
    # This ensures zero bets always returns to original seed-based odds
    init_a = matchup.initial_odds_a if matchup.initial_odds_a else matchup.odds_a
    init_b = matchup.initial_odds_b if matchup.initial_odds_b else matchup.odds_b
    implied_a = 1.0 / init_a
    implied_b = 1.0 / init_b
    total_implied = implied_a + implied_b
    base_a = BASE_POOL * (implied_a / total_implied)
    base_b = BASE_POOL * (implied_b / total_implied)

    # Sum of actual money bet on each side
    result = (
        db.query(
            models.Bet.pick,
            func.sum(models.Bet.amount).label("total"),
        )
        .filter(models.Bet.matchup_id == matchup_id)
        .group_by(models.Bet.pick)
        .all()
    )

    totals = {"A": base_a, "B": base_b}
    for row in result:
        totals[row.pick] = totals[row.pick] + (row.total or 0)

    pool = totals["A"] + totals["B"]

    prob_a = totals["A"] / pool
    prob_b = totals["B"] / pool

    prob_a_vig = prob_a * (1 + VIG)
    prob_b_vig = prob_b * (1 + VIG)

    odds_a = max(MIN_ODDS, min(MAX_ODDS, 1 / prob_a_vig))
    odds_b = max(MIN_ODDS, min(MAX_ODDS, 1 / prob_b_vig))

    return round(odds_a, 2), round(odds_b, 2)
