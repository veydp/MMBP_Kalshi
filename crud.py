from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, hashed_password: str):
    is_admin = db.query(models.User).count() < 3  # First 3 accounts are admins
    user = models.User(username=username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session):
    return db.query(models.User).order_by(models.User.created_at.asc()).all()


def delete_user(db: Session, user_id: int, current_user_id: int):
    """Delete a user and refund nothing — removes all their bets too."""
    if user_id == current_user_id:
        return False, "Cannot delete yourself"
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False, "User not found"
    if user.is_admin:
        return False, "Cannot delete an admin account"
    # Delete their bets
    db.query(models.Bet).filter(models.Bet.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return True, "Deleted"


# ── Matchups ──────────────────────────────────────────────────────────────────

def get_all_matchups(db: Session):
    return db.query(models.Matchup).order_by(
        models.Matchup.tournament_id.asc().nullslast(),
        models.Matchup.round_number.asc().nullslast(),
        models.Matchup.bracket_position.asc().nullslast(),
        models.Matchup.created_at.desc()
    ).all()


def get_matchup(db: Session, matchup_id: int):
    return db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()


def create_matchup(db: Session, matchup: schemas.MatchupCreate):
    data = matchup.model_dump()
    db_matchup = models.Matchup(**data)
    db_matchup.initial_odds_a = data.get('odds_a', 2.0)
    db_matchup.initial_odds_b = data.get('odds_b', 2.0)
    db.add(db_matchup)
    db.commit()
    db.refresh(db_matchup)
    return db_matchup


def update_odds(db: Session, matchup_id: int, odds_a: float, odds_b: float):
    matchup = get_matchup(db, matchup_id)
    matchup.odds_a = round(odds_a, 2)
    matchup.odds_b = round(odds_b, 2)
    db.commit()
    db.refresh(matchup)
    return matchup


def lock_matchup(db: Session, matchup_id: int):
    matchup = get_matchup(db, matchup_id)
    matchup.status = "locked"
    db.commit()
    db.refresh(matchup)
    return matchup


def settle_matchup(db: Session, matchup_id: int, winner: str):
    matchup = get_matchup(db, matchup_id)
    matchup.status = "settled"
    matchup.winner = winner
    matchup.winner_name = matchup.player_a if winner == "A" else matchup.player_b
    db.commit()

    # Settle bets
    bets = db.query(models.Bet).filter(
        models.Bet.matchup_id == matchup_id,
        models.Bet.settled == False,
    ).all()
    for bet in bets:
        bet.settled = True
        bet.won = bet.pick == winner
        if bet.won:
            user = db.query(models.User).filter(models.User.id == bet.user_id).first()
            user.balance += bet.potential_payout

    db.commit()
    db.refresh(matchup)
    return matchup


# ── Bets ──────────────────────────────────────────────────────────────────────

def create_bet(db: Session, user_id: int, bet: schemas.BetCreate):
    matchup = get_matchup(db, bet.matchup_id)
    odds = matchup.odds_a if bet.pick == "A" else matchup.odds_b
    payout = round(bet.amount * odds, 2)

    db_bet = models.Bet(
        user_id=user_id,
        matchup_id=bet.matchup_id,
        pick=bet.pick,
        amount=bet.amount,
        odds_at_bet=odds,
        potential_payout=payout,
    )
    db.add(db_bet)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.balance -= bet.amount

    db.commit()
    db.refresh(db_bet)
    return db_bet


def get_matchup_bets(db: Session, matchup_id: int):
    """Return all bets for a matchup with username attached."""
    bets = (
        db.query(models.Bet, models.User.username)
        .join(models.User, models.Bet.user_id == models.User.id)
        .filter(models.Bet.matchup_id == matchup_id)
        .order_by(models.Bet.created_at.desc())
        .all()
    )
    result = []
    for bet, username in bets:
        result.append({
            "id": bet.id,
            "matchup_id": bet.matchup_id,
            "username": username,
            "pick": bet.pick,
            "amount": bet.amount,
            "odds_at_bet": bet.odds_at_bet,
            "potential_payout": bet.potential_payout,
            "settled": bet.settled,
            "won": bet.won,
            "created_at": bet.created_at,
        })
    return result


def delete_bet(db: Session, bet_id: int):
    """Delete a bet and refund the user if unsettled."""
    bet = db.query(models.Bet).filter(models.Bet.id == bet_id).first()
    if not bet:
        return False, "Bet not found"
    if bet.settled:
        return False, "Cannot delete a settled bet"
    # Refund the stake
    user = db.query(models.User).filter(models.User.id == bet.user_id).first()
    if user:
        user.balance += bet.amount
    db.delete(bet)
    db.commit()
    return True, "Deleted and refunded"


def get_user_bets(db: Session, user_id: int):
    return (
        db.query(models.Bet)
        .filter(models.Bet.user_id == user_id)
        .order_by(models.Bet.created_at.desc())
        .all()
    )


# ── Leaderboard ───────────────────────────────────────────────────────────────

def get_leaderboard(db: Session):
    users = db.query(models.User).filter(models.User.is_admin == False).all()
    entries = []
    for user in users:
        bets = db.query(models.Bet).filter(models.Bet.user_id == user.id).all()
        entries.append({
            "username": user.username,
            "balance": user.balance,
            "total_bets": len(bets),
            "total_won": sum(1 for b in bets if b.won),
        })
    return sorted(entries, key=lambda x: x["balance"], reverse=True)
