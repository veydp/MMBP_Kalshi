from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    balance: float
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool


# ── Matchups ──────────────────────────────────────────────────────────────────

class MatchupCreate(BaseModel):
    player_a: str
    player_b: str
    sport: str = "Sport"
    odds_a: float = Field(default=2.0, gt=1.0)
    odds_b: float = Field(default=2.0, gt=1.0)


class MatchupOut(BaseModel):
    id: int
    player_a: str
    player_b: str
    sport: str
    odds_a: float
    odds_b: float
    status: str
    winner: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MatchupResult(BaseModel):
    winner: str  # "A" or "B"


class OddsUpdate(BaseModel):
    odds_a: float = Field(gt=1.0)
    odds_b: float = Field(gt=1.0)


# ── Bets ──────────────────────────────────────────────────────────────────────

class BetCreate(BaseModel):
    matchup_id: int
    pick: str        # "A" or "B"
    amount: float = Field(gt=0)


class BetOut(BaseModel):
    id: int
    matchup_id: int
    pick: str
    amount: float
    odds_at_bet: float
    potential_payout: float
    settled: bool
    won: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    username: str
    balance: float
    total_bets: int
    total_won: int
