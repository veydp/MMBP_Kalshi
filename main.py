from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import get_db, engine
import models
import schemas
import crud
import bracket_engine as be
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from odds_engine import recalculate_odds
from connection_manager import ConnectionManager

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tournament Betting Market")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

manager = ConnectionManager()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html") as f:
        return f.read()


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud.create_user(db, user.username, get_password_hash(user.password))


@app.post("/api/login", response_model=schemas.Token)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer", "is_admin": db_user.is_admin}


@app.get("/api/me", response_model=schemas.UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user


# ── Tournaments ───────────────────────────────────────────────────────────────

@app.get("/api/tournaments", response_model=List[schemas.TournamentOut])
def get_tournaments(db: Session = Depends(get_db)):
    return be.get_all_tournaments(db)


@app.post("/api/tournaments", response_model=schemas.TournamentOut)
def create_tournament(t: schemas.TournamentCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return be.create_tournament(db, t.name)


@app.post("/api/tournaments/setup")
async def setup_round(setup: schemas.TournamentSetup, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    """Bulk-create matchups for a round and wire up bracket links."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    created = []
    for entry in setup.matchups:
        m = be.add_matchup_to_tournament(
            db,
            tournament_id=setup.tournament_id,
            player_a=entry.player_a,
            player_b=entry.player_b,
            seed_a=entry.seed_a,
            seed_b=entry.seed_b,
            round_number=setup.round_number,
            bracket_position=entry.bracket_position,
            sport=setup.sport,
        )
        created.append(m)

    await manager.broadcast({"type": "new_round", "round": setup.round_number,
                             "round_name": be.ROUND_NAMES.get(setup.round_number, f"Round {setup.round_number}")})
    return {"created": len(created), "matchups": [m.id for m in created]}


@app.post("/api/tournaments/{tournament_id}/confirm_next_round")
async def confirm_next_round(tournament_id: int, db: Session = Depends(get_db),
                              current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchups = be.confirm_next_round(db, tournament_id)
    t = be.get_tournament(db, tournament_id)
    await manager.broadcast({
        "type": "round_confirmed",
        "tournament_id": tournament_id,
        "round": t.current_round,
        "round_name": be.ROUND_NAMES.get(t.current_round, f"Round {t.current_round}"),
    })
    return {"ok": True, "round": t.current_round}


@app.get("/api/tournaments/{tournament_id}/next_round_status")
def next_round_status(tournament_id: int, db: Session = Depends(get_db)):
    t = be.get_tournament(db, tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    round_complete = be.check_round_complete(db, tournament_id, t.current_round)
    next_round, next_matchups = be.get_pending_next_round(db, tournament_id)
    return {
        "current_round": t.current_round,
        "current_round_name": be.ROUND_NAMES.get(t.current_round, f"Round {t.current_round}"),
        "round_complete": round_complete,
        "next_round": next_round,
        "next_round_name": be.ROUND_NAMES.get(next_round, f"Round {next_round}") if next_round else None,
        "next_round_ready": bool(next_matchups),
        "next_matchup_count": len(next_matchups) if next_matchups else 0,
    }


# ── Matchups ──────────────────────────────────────────────────────────────────

@app.get("/api/matchups", response_model=List[schemas.MatchupOut])
def get_matchups(db: Session = Depends(get_db)):
    return crud.get_all_matchups(db)


@app.post("/api/matchups", response_model=schemas.MatchupOut)
def create_matchup(matchup: schemas.MatchupCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return crud.create_matchup(db, matchup)


@app.patch("/api/matchups/{matchup_id}/lock")
async def lock_matchup(matchup_id: int, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchup = crud.lock_matchup(db, matchup_id)
    await manager.broadcast({"type": "matchup_locked", "matchup_id": matchup_id})
    return {"ok": True}


@app.patch("/api/matchups/{matchup_id}/result")
async def set_result(matchup_id: int, result: schemas.MatchupResult,
                     db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchup = crud.settle_matchup(db, matchup_id, result.winner)

    # Auto-advance winner in bracket
    if matchup.tournament_id:
        be.advance_winner(db, matchup)
        # Check if round is complete
        if be.check_round_complete(db, matchup.tournament_id, matchup.round_number):
            await manager.broadcast({
                "type": "round_complete",
                "tournament_id": matchup.tournament_id,
                "round": matchup.round_number,
                "round_name": be.ROUND_NAMES.get(matchup.round_number, f"Round {matchup.round_number}"),
            })

    await manager.broadcast({"type": "matchup_settled", "matchup_id": matchup_id,
                             "winner": result.winner, "winner_name": matchup.winner_name})
    return {"ok": True}


@app.patch("/api/matchups/{matchup_id}/odds")
async def admin_set_odds(matchup_id: int, odds: schemas.OddsUpdate,
                         db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchup = crud.update_odds(db, matchup_id, odds.odds_a, odds.odds_b)
    await manager.broadcast({"type": "odds_update", "matchup_id": matchup_id,
                             "odds_a": matchup.odds_a, "odds_b": matchup.odds_b})
    return {"ok": True}


# ── Bracket link wiring ───────────────────────────────────────────────────────

@app.post("/api/matchups/link")
def link_matchups(matchup_id: int, next_matchup_id: int, next_slot: str,
                  db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    be.link_matchups(db, matchup_id, next_matchup_id, next_slot)
    return {"ok": True}


# ── Bets ──────────────────────────────────────────────────────────────────────

@app.post("/api/bets", response_model=schemas.BetOut)
async def place_bet(bet: schemas.BetCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    matchup = crud.get_matchup(db, bet.matchup_id)
    if not matchup:
        raise HTTPException(status_code=404, detail="Matchup not found")
    if matchup.status != "open":
        raise HTTPException(status_code=400, detail="Betting is closed for this matchup")
    if current_user.balance < bet.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    db_bet = crud.create_bet(db, current_user.id, bet)
    new_odds_a, new_odds_b = recalculate_odds(db, bet.matchup_id)
    crud.update_odds(db, bet.matchup_id, new_odds_a, new_odds_b)
    await manager.broadcast({"type": "odds_update", "matchup_id": bet.matchup_id,
                             "odds_a": new_odds_a, "odds_b": new_odds_b})
    return db_bet


@app.get("/api/bets/me", response_model=List[schemas.BetOut])
def my_bets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_user_bets(db, current_user.id)


# ── Leaderboard ───────────────────────────────────────────────────────────────

@app.get("/api/leaderboard", response_model=List[schemas.LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    return crud.get_leaderboard(db)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
