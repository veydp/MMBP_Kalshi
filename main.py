from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio

from database import get_db, engine
import models
import schemas
import crud
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from odds_engine import recalculate_odds
from connection_manager import ConnectionManager

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tournament Betting Market")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    hashed = get_password_hash(user.password)
    return crud.create_user(db, user.username, hashed)


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


# ── Matchups ──────────────────────────────────────────────────────────────────

@app.get("/api/matchups", response_model=List[schemas.MatchupOut])
def get_matchups(db: Session = Depends(get_db)):
    return crud.get_all_matchups(db)


@app.post("/api/matchups", response_model=schemas.MatchupOut)
def create_matchup(
    matchup: schemas.MatchupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return crud.create_matchup(db, matchup)


@app.patch("/api/matchups/{matchup_id}/result")
async def set_result(
    matchup_id: int,
    result: schemas.MatchupResult,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchup = crud.settle_matchup(db, matchup_id, result.winner)
    await manager.broadcast({"type": "matchup_settled", "matchup_id": matchup_id, "winner": result.winner})
    return {"ok": True}


@app.patch("/api/matchups/{matchup_id}/odds")
async def admin_set_odds(
    matchup_id: int,
    odds: schemas.OddsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    matchup = crud.update_odds(db, matchup_id, odds.odds_a, odds.odds_b)
    await manager.broadcast({
        "type": "odds_update",
        "matchup_id": matchup_id,
        "odds_a": matchup.odds_a,
        "odds_b": matchup.odds_b,
    })
    return {"ok": True}


# ── Bets ──────────────────────────────────────────────────────────────────────

@app.post("/api/bets", response_model=schemas.BetOut)
async def place_bet(
    bet: schemas.BetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    matchup = crud.get_matchup(db, bet.matchup_id)
    if not matchup:
        raise HTTPException(status_code=404, detail="Matchup not found")
    if matchup.status != "open":
        raise HTTPException(status_code=400, detail="Betting is closed for this matchup")
    if current_user.balance < bet.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if bet.amount <= 0:
        raise HTTPException(status_code=400, detail="Bet amount must be positive")

    db_bet = crud.create_bet(db, current_user.id, bet)

    # Recalculate odds based on new bet volume
    new_odds_a, new_odds_b = recalculate_odds(db, bet.matchup_id)
    crud.update_odds(db, bet.matchup_id, new_odds_a, new_odds_b)

    await manager.broadcast({
        "type": "odds_update",
        "matchup_id": bet.matchup_id,
        "odds_a": new_odds_a,
        "odds_b": new_odds_b,
    })
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
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
