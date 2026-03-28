"""
Bracket Engine
--------------
Handles March Madness style bracket automation.
"""

from sqlalchemy.orm import Session
import models

ROUND_NAMES = {
    0: "Play-In",
    1: "Round of 64",
    2: "Round of 32",
    3: "Sweet 16",
    4: "Elite 8",
    5: "Final Four",
    6: "Championship",
}

SEED_ODDS = {
    (1, 16): (1.05, 12.0),
    (2, 15): (1.15, 7.0),
    (3, 14): (1.25, 5.0),
    (4, 13): (1.35, 4.0),
    (5, 12): (1.50, 3.0),
    (6, 11): (1.65, 2.5),
    (7, 10): (1.80, 2.2),
    (8, 9):  (1.95, 2.0),
}


def get_seed_odds(seed_a, seed_b):
    if seed_a and seed_b:
        key = (min(seed_a, seed_b), max(seed_a, seed_b))
        if key in SEED_ODDS:
            base_a, base_b = SEED_ODDS[key]
            if seed_a > seed_b:
                return base_b, base_a
            return base_a, base_b
    return 2.0, 2.0


def get_tournament(db: Session, tournament_id: int):
    return db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()


def get_all_tournaments(db: Session):
    return db.query(models.Tournament).order_by(models.Tournament.created_at.desc()).all()


def create_tournament(db: Session, name: str):
    t = models.Tournament(name=name, current_round=0, status="active")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def add_matchup_to_tournament(db: Session, tournament_id: int, player_a: str, player_b: str,
                               seed_a: int, seed_b: int, round_number: int, bracket_position: int,
                               sport: str = "MMBP 2026"):
    odds_a, odds_b = get_seed_odds(seed_a, seed_b)
    # New matchups that are NOT the current round start as "pending" so they don't show as bettable yet
    t = get_tournament(db, tournament_id)
    current_round = t.current_round if t else 0
    status = "open" if round_number <= current_round else "pending"
    m = models.Matchup(
        player_a=player_a,
        player_b=player_b,
        seed_a=seed_a,
        seed_b=seed_b,
        sport=sport,
        odds_a=odds_a,
        odds_b=odds_b,
        status=status,
        tournament_id=tournament_id,
        round_number=round_number,
        bracket_position=bracket_position,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def link_matchups(db: Session, matchup_id: int, next_matchup_id: int, next_slot: str):
    m = db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()
    m.next_matchup_id = next_matchup_id
    m.next_slot = next_slot
    db.commit()


def advance_winner(db: Session, matchup: models.Matchup):
    """Place winner name into the next matchup slot. If both slots filled, open betting."""
    if not matchup.next_matchup_id or not matchup.winner_name:
        return
    next_m = db.query(models.Matchup).filter(models.Matchup.id == matchup.next_matchup_id).first()
    if not next_m:
        return

    winner_seed = matchup.seed_a if matchup.winner == "A" else matchup.seed_b

    if matchup.next_slot == "A":
        next_m.player_a = matchup.winner_name
        next_m.seed_a = winner_seed
    else:
        next_m.player_b = matchup.winner_name
        next_m.seed_b = winner_seed

    # Recalculate odds now that we know both seeds
    if next_m.seed_a and next_m.seed_b:
        odds_a, odds_b = get_seed_odds(next_m.seed_a, next_m.seed_b)
        next_m.odds_a = odds_a
        next_m.odds_b = odds_b

    # If neither player is still a TBD placeholder, open the matchup for betting
    a_ready = next_m.player_a and "TBD" not in next_m.player_a and "winner" not in next_m.player_a.lower()
    b_ready = next_m.player_b and "TBD" not in next_m.player_b and "winner" not in next_m.player_b.lower()
    if a_ready and b_ready and next_m.status == "pending":
        next_m.status = "open"

    db.commit()


def delete_matchup(db: Session, matchup_id: int) -> bool:
    """Delete a matchup and its bets. Returns False if matchup has settled bets."""
    m = db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()
    if not m:
        return False
    # Refund any unsettled bets
    bets = db.query(models.Bet).filter(models.Bet.matchup_id == matchup_id).all()
    for bet in bets:
        if not bet.settled:
            user = db.query(models.User).filter(models.User.id == bet.user_id).first()
            if user:
                user.balance += bet.amount
        db.delete(bet)
    db.delete(m)
    db.commit()
    return True


def fix_matchup_round(db: Session, matchup_id: int, round_number: int):
    """Fix a matchup's round number."""
    m = db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()
    if not m:
        return None
    m.round_number = round_number
    db.commit()
    db.refresh(m)
    return m


def check_round_complete(db: Session, tournament_id: int, round_number: int) -> bool:
    matchups = db.query(models.Matchup).filter(
        models.Matchup.tournament_id == tournament_id,
        models.Matchup.round_number == round_number,
        models.Matchup.status != "pending",
    ).all()
    if not matchups:
        return False
    return all(m.status == "settled" for m in matchups)


def get_round_matchups(db: Session, tournament_id: int, round_number: int):
    return db.query(models.Matchup).filter(
        models.Matchup.tournament_id == tournament_id,
        models.Matchup.round_number == round_number,
    ).order_by(models.Matchup.bracket_position).all()


def get_pending_next_round(db: Session, tournament_id: int):
    t = get_tournament(db, tournament_id)
    if not t:
        return None, None
    next_round = t.current_round + 1
    matchups = get_round_matchups(db, tournament_id, next_round)
    return next_round, matchups


def confirm_next_round(db: Session, tournament_id: int):
    t = get_tournament(db, tournament_id)
    next_round = t.current_round + 1
    matchups = get_round_matchups(db, tournament_id, next_round)
    for m in matchups:
        if m.status == "pending":
            m.status = "open"
    t.current_round = next_round
    db.commit()
    return matchups
