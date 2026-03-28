from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, hashed_password: str):
    # First user registered becomes admin
    is_admin = db.query(models.User).count() == 0
    user = models.User(username=username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Matchups ──────────────────────────────────────────────────────────────────

def get_all_matchups(db: Session):
    return db.query(models.Matchup).order_by(models.Matchup.created_at.desc()).all()


def get_matchup(db: Session, matchup_id: int):
    return db.query(models.Matchup).filter(models.Matchup.id == matchup_id).first()


def create_matchup(db: Session, matchup: schemas.MatchupCreate):
    db_matchup = models.Matchup(**matchup.model_dump())
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


def settle_matchup(db: Session, matchup_id: int, winner: str):
    matchup = get_matchup(db, matchup_id)
    matchup.status = "settled"
    matchup.winner = winner
    db.commit()

    # Settle all bets for this matchup
    bets = db.query(models.Bet).filter(
        models.Bet.matchup_id == matchup_id,
        models.Bet.settled == False,
    ).all()

    for bet in bets:
        bet.settled = True
        bet.won = bet.pick == winner
        user = db.query(models.User).filter(models.User.id == bet.user_id).first()
        if bet.won:
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

    # Deduct stake from user balance
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.balance -= bet.amount

    db.commit()
    db.refresh(db_bet)
    return db_bet


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
        total_bets = len(bets)
        total_won = sum(1 for b in bets if b.won)
        entries.append({
            "username": user.username,
            "balance": user.balance,
            "total_bets": total_bets,
            "total_won": total_won,
        })
    return sorted(entries, key=lambda x: x["balance"], reverse=True)
